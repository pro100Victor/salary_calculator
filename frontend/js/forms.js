/** Общие средства форм: сообщение у поля, повторная отправка, сохранение ввода. */
import { ApiError } from "./api.js";

export const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);

export function field(name, label, type = "text", value = "", attributes = "") {
  return `<label>${label}<input name="${name}" type="${type}" value="${escapeHtml(value)}" ${attributes}><small class="field-error" data-error="${name}"></small></label>`;
}

export function showErrors(form, error) {
  form.querySelectorAll("[data-error]").forEach(node => { node.textContent = ""; });
  form.querySelectorAll('[aria-invalid="true"]').forEach(node => node.removeAttribute("aria-invalid"));
  form.querySelector(".form-error").textContent = error.message;
  for (const [key, message] of Object.entries(error.fields || {})) {
    const input = form.elements.namedItem(key);
    const hint = [...form.querySelectorAll("[data-error]")].find(node => node.dataset.error === key);
    if (input) input.setAttribute("aria-invalid", "true");
    if (hint) hint.textContent = message;
  }
  form.querySelector('[aria-invalid="true"]')?.focus();
}

export function bindForm(form, submit, handleSessionError) {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (form.dataset.busy || !form.reportValidity()) return;
    form.dataset.busy = "true";
    const button = form.querySelector('[type="submit"]');
    const label = button.textContent;
    button.disabled = true;
    button.textContent = "Сохранение…";
    try {
      await submit(Object.fromEntries(new FormData(form)));
    } catch (error) {
      showErrors(form, error);
      if (error instanceof ApiError && error.status === 401) handleSessionError?.();
    } finally {
      delete form.dataset.busy;
      button.disabled = false;
      button.textContent = label;
    }
  });
}

export function integer(value, fieldName) {
  if (!/^-?\d+$/.test(String(value))) throw new ApiError("Введите целое число", { [fieldName]: "Введите целое число" });
  const number = Number(value);
  if (!Number.isSafeInteger(number)) throw new ApiError("Число слишком велико", { [fieldName]: "Число слишком велико" });
  return number;
}
