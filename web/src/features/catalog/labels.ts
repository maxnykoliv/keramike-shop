export const KIND_LABELS: Record<string, string> = {
  tile: "Плитка", mosaic: "Мозаїка", decor: "Декор", glue: "Клей", grout: "Затирка",
  primer: "Ґрунтовка", waterproofing: "Гідроізоляція", accessory: "Аксесуари",
};
export const ROOM_LABELS: Record<string, string> = {
  bathroom: "Ванна", toilet: "Туалет", kitchen: "Кухня", hallway: "Коридор", terrace: "Тераса", living: "Житлова кімната",
};
export const APPLICATION_LABELS: Record<string, string> = { floor: "Підлога", wall: "Стіна", outdoor: "Вулиця" };
export const MATERIAL_LABELS: Record<string, string> = { ceramic: "Кераміка", porcelain: "Керамограніт" };
export const SORT_OPTIONS = [
  { value: "", label: "За назвою" },
  { value: "-new", label: "Спершу нові" },
  { value: "price", label: "Спершу дешевші" },
  { value: "-price", label: "Спершу дорожчі" },
];
