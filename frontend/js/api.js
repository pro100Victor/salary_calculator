/** HTTP-транспорт. Деньги остаются строками, расчёты выполняет сервер. */
export class ApiError extends Error {
  constructor(message, fields = {}, status = 0) {
    super(message);
    this.fields = fields;
    this.status = status;
  }
}

export async function request(path, method = "GET", body) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method, credentials: "same-origin",
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Нет связи с сервером. Введённые данные сохранены в форме.");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(data.message || "Не удалось выполнить действие", data.fields, response.status);
  return data;
}
