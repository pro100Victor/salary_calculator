/** Сценарии бухгалтера: навигация, формы и вызовы API существующих сервисов. */
import { request } from "./api.js";
import { bindForm, escapeHtml as e, field, integer } from "./forms.js";
import { actions, employeeForm, money, payslip, renderEmployees, renderHome, renderPayroll, renderSettings, renderTimesheet } from "./render.js";

const titles = { home: ["Salary Calculator", "Главная"], employees: ["Сотрудники", "Карточки сотрудников предприятия"], timesheet: ["Табель рабочего времени", "Смены и дни отсутствия"], payroll: ["Расчётная ведомость", "Начисления, удержания и расчётные листки"], settings: ["Настройки предприятия", "Реквизиты, должности и тарифы"] };
const months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
const now = new Date();
let page = "home", directory = { employees: [], positions: [], organization: null }, period = null;
let periodVersion = 0;
let actionBusy = false;
const dialog = document.querySelector("#form-dialog");
const loginDialog = document.querySelector("#login-dialog");
const yearInput = document.querySelector("#year"), monthInput = document.querySelector("#month");
yearInput.value = now.getFullYear();
monthInput.innerHTML = months.map((name, index) => `<option value="${index + 1}" ${index === now.getMonth() ? "selected" : ""}>${name}</option>`).join("");

function notify(message, error = false) {
  const node = document.querySelector("#notice");
  node.textContent = message;
  node.className = `notice${error ? " error" : ""}`;
  node.hidden = false;
}

function showLogin() {
  if (!loginDialog.open) loginDialog.showModal();
}

function handleError(error) {
  notify(error.message, true);
  if (error.status === 401) showLogin();
}

async function refreshDirectory() {
  directory = await request("/state");
  document.querySelector("#organization-name").textContent = directory.organization?.name || "Предприятие не настроено";
  document.querySelector("#storage-mode").textContent = directory.storage_mode;
}

function periodPath() {
  if (!period) throw new Error("Сначала откройте расчётный период");
  return `/periods/${period.period.year}/${period.period.month}`;
}

async function loadPeriod() {
  const version = ++periodVersion;
  period = null;
  render();
  const year = integer(yearInput.value, "year"), month = integer(monthInput.value, "month");
  if (!yearInput.reportValidity()) throw new Error("Укажите год от 1 до 9999");
  const data = await request(`/periods/${year}/${month}`);
  if (version === periodVersion) {
    period = data;
    render();
  }
}

function render() {
  document.querySelector("#home").innerHTML = renderHome(directory);
  document.querySelector("#employees").innerHTML = renderEmployees(directory);
  document.querySelector("#settings").innerHTML = renderSettings(directory);
  document.querySelector("#timesheet").innerHTML = renderTimesheet(directory, period);
  document.querySelector("#payroll").innerHTML = renderPayroll(period);
  document.querySelector("#period-badge").textContent = period ? `${String(period.period.month).padStart(2, "0")}.${period.period.year} · ${period.timesheet?.closed ? "Закрыт" : "Открыт"}` : "Период не открыт";
  bindForm(document.querySelector("#organization-form"), async data => {
    await request("/organization", "PUT", data);
    await refreshDirectory();
    render();
    notify("Реквизиты предприятия сохранены");
  }, showLogin);
}

async function navigate(target) {
  if (!(target in titles)) return;
  page = target;
  document.querySelectorAll(".page").forEach(node => { node.hidden = node.id !== target; });
  document.querySelectorAll("[data-page]").forEach(node => node.classList.toggle("active", node.dataset.page === target));
  document.querySelector("#page-title").textContent = titles[target][0];
  document.querySelector("#page-subtitle").textContent = titles[target][1];
  document.querySelector("#period-controls").hidden = !["timesheet", "payroll"].includes(target);
  document.querySelector("#notice").hidden = true;
  if (["timesheet", "payroll"].includes(target) && !period) await loadPeriod();
}

function openForm(title, html, submit) {
  document.querySelector("#dialog-title").textContent = title;
  document.querySelector("#dialog-content").innerHTML = html;
  dialog.showModal();
  const form = dialog.querySelector("form");
  if (form) bindForm(form, submit, showLogin);
  return form;
}

function openEmployee(id) {
  if (!directory.organization || !directory.positions.length) throw new Error("Сначала заполните реквизиты предприятия и добавьте должности в настройках");
  const old = directory.employees.find(item => item.employee_id === id);
  const form = openForm(old ? "Изменить карточку" : "Добавить сотрудника", employeeForm(directory, old), async data => {
    data.experience_years = integer(data.experience_years, "experience_years");
    await request(old ? `/employees/${id}` : "/employees", old ? "PUT" : "POST", data);
    dialog.close();
    await refreshDirectory();
    render();
    notify(old ? "Карточка сотрудника обновлена" : "Сотрудник добавлен");
  });
  let version = 0;
  async function updateRate() {
    const current = ++version;
    const position = form.elements.position.value, years = form.elements.experience_years.value;
    const preview = document.querySelector("#rate-preview");
    preview.textContent = "—";
    if (!position || !/^[0-9]+$/.test(years)) return;
    try {
      const result = await request(`/rate?${new URLSearchParams({ position, experience_years: years })}`);
      if (current === version && preview.isConnected) preview.textContent = money(result.rate_per_shift);
    } catch (error) {
      if (current === version && preview.isConnected) preview.textContent = "Проверьте должность и стаж";
      if (error.status === 401) showLogin();
    }
  }
  form.elements.position.addEventListener("change", updateRate);
  form.elements.experience_years.addEventListener("input", updateRate);
  updateRate();
}

function openPosition(index) {
  if (!directory.organization) throw new Error("Сначала сохраните реквизиты предприятия");
  const item = directory.positions[index] || {};
  openForm("Должность и тариф", `<form><div class="form-grid">${field("name", "Название должности", "text", item.name, "required maxlength=200")}${field("base_rate", "Базовая ставка за смену, руб.", "number", item.base_rate, "required min=0.01 max=1000000000 step=0.01")}${field("seniority_percent", "Надбавка за год стажа, %", "number", item.seniority_percent ?? "0", "required min=0 max=100 step=any")}</div><p class="hint">Название определяет должность. Для обновления тарифа оставьте прежнее название.</p>${actions("Сохранить тариф")}</form>`, async data => {
    await request("/positions", "PUT", data);
    dialog.close(); await refreshDirectory(); render(); notify("Тариф сохранён");
  });
}

function openDismiss(id) {
  const employee = directory.employees.find(item => item.employee_id === id);
  openForm("Увольнение сотрудника", `<p>${e(employee.full_name)}</p><form>${field("dismissal_date", "Дата увольнения", "date", "", `required min="${employee.hire_date}"`)}${actions("Уволить сотрудника")}</form>`, async data => {
    await request(`/employees/${id}/dismiss`, "POST", data);
    dialog.close(); await refreshDirectory(); render(); notify("Дата увольнения сохранена. История сотрудника остаётся в системе.");
  });
}

function openEntry(id) {
  const currentPath = periodPath(), row = period.timesheet.entries[id] || {};
  const employee = directory.employees.find(item => item.employee_id === id);
  openForm("Строка табеля", `<p>${e(employee.full_name)} · норма ${period.norm} смен</p><form><div class="form-grid">${field("worked_shifts", "Отработано смен", "number", row.worked_shifts ?? "", `required min=0 max=${period.norm} step=1`)}${field("sick_days", "Больничный, дней", "number", row.sick_days ?? "0", `required min=0 max=${period.norm} step=1`)}${field("vacation_days", "Отпуск, дней", "number", row.vacation_days ?? "0", `required min=0 max=${period.norm} step=1`)}</div><p class="hint">Сумма смен и дней отсутствия не должна превышать норму.</p>${actions("Сохранить строку")}</form>`, async data => {
    Object.keys(data).forEach(key => { data[key] = integer(data[key], key); });
    period = await request(`${currentPath}/entries/${id}`, "PUT", data);
    dialog.close(); render(); notify("Строка табеля сохранена");
  });
}

function openNorm() {
  const currentPath = periodPath();
  openForm("Норма смен", `<form>${field("shifts", "Норма на выбранный месяц", "number", period.norm, `required min=1 max=${new Date(period.period.year, period.period.month, 0).getDate()} step=1`)}<p class="hint">Норму можно изменить только до формирования табеля.</p>${actions("Сохранить норму")}</form>`, async data => {
    period = await request(`${currentPath}/norm`, "PUT", { shifts: integer(data.shifts, "shifts") });
    dialog.close(); render(); notify("Норма смен сохранена");
  });
}

async function runAction(action) {
  if (action === "add-employee") return openEmployee();
  if (action === "add-position") return openPosition();
  if (action === "norm") return openNorm();
  if (action === "generate") {
    period = await request(`${periodPath()}/timesheet`, "POST");
  } else if (action === "calculate") {
    const replace = Boolean(period?.statement);
    if (replace && !confirm("Пересчитать ведомость? Прежний результат будет заменён только после успешного расчёта.")) return;
    period = await request(`${periodPath()}/statement`, "POST", { replace_existing: replace });
  } else if (action === "close-period") {
    if (!confirm("Закрыть период? После закрытия нельзя менять табель и пересчитывать зарплату.")) return;
    period = await request(`${periodPath()}/close`, "POST");
  }
  render(); notify("Действие выполнено");
}

document.addEventListener("click", async event => {
  const button = event.target.closest("button, [data-go]");
  if (!button || button.disabled) return;
  try {
    if (button.dataset.page || button.dataset.go) await navigate(button.dataset.page || button.dataset.go);
    else if (button.hasAttribute("data-edit")) openEmployee(Number(button.dataset.edit));
    else if (button.hasAttribute("data-dismiss")) openDismiss(Number(button.dataset.dismiss));
    else if (button.hasAttribute("data-position")) openPosition(Number(button.dataset.position));
    else if (button.hasAttribute("data-entry")) openEntry(Number(button.dataset.entry));
    else if (button.hasAttribute("data-payslip")) {
      const result = period.statement.results.find(item => item.employee.employee_id === Number(button.dataset.payslip));
      openForm("Расчётный листок", payslip(result, period.statement));
    } else if (button.hasAttribute("data-print")) window.print();
    else if (button.hasAttribute("data-cancel") || button.id === "close-dialog") {
      if (!dialog.querySelector('[data-busy="true"]')) dialog.close();
    } else if (button.dataset.action) {
      if (actionBusy) return;
      actionBusy = true;
      button.disabled = true;
      const controls = [...document.querySelectorAll("#period-controls input, #period-controls select, #period-controls button")];
      controls.forEach(control => { control.disabled = true; });
      try { await runAction(button.dataset.action); } finally {
        button.disabled = false;
        controls.forEach(control => { control.disabled = false; });
        actionBusy = false;
      }
    }
  } catch (error) { handleError(error); }
});

document.addEventListener("input", event => {
  if (event.target.id === "employee-search") {
    const query = event.target.value, caret = event.target.selectionStart;
    document.querySelector("#employees").innerHTML = renderEmployees(directory, query);
    const search = document.querySelector("#employee-search");
    search.focus(); search.setSelectionRange(caret, caret);
  }
});

for (const input of [yearInput, monthInput]) input.addEventListener("change", () => {
  ++periodVersion; period = null; render();
});
document.querySelector("#load-period").addEventListener("click", () => loadPeriod().catch(handleError));
document.querySelector("#logout").addEventListener("click", async () => {
  try {
    await request("/logout", "POST");
    directory = { employees: [], positions: [], organization: null }; period = null;
    render(); showLogin();
  } catch (error) { handleError(error); }
});
loginDialog.addEventListener("cancel", event => event.preventDefault());
dialog.addEventListener("cancel", event => {
  if (dialog.querySelector('[data-busy="true"]')) event.preventDefault();
});
bindForm(document.querySelector("#login-form"), async data => {
  await request("/login", "POST", data);
  loginDialog.close();
  document.querySelector("#login-form").elements.password.value = "";
  await refreshDirectory(); render();
  if (["timesheet", "payroll"].includes(page)) await loadPeriod();
  notify("Вход выполнен");
});
render();
refreshDirectory().then(render).catch(error => {
  if (error.status === 401) showLogin(); else handleError(error);
});
