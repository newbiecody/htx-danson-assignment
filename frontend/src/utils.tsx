export const formatDateToHumanReadable = (timestamp: number) => {
  const date = new Date(timestamp);

  const day = date.getDate();
  const month = date.getMonth() + 1;
  const year = date.getFullYear();

  const dateString = [day, month, year].join("-");

  let hours = date.getHours();
  const minutes = date.getMinutes().toString().padStart(2, "0");
  const seconds = date.getSeconds().toString().padStart(2, "0");

  let timeString;
  let period = "";

  period = hours >= 12 ? " PM" : " AM";
  hours = hours % 12 || 12;

  timeString = `${hours}:${minutes}:${seconds}`;
  timeString += period;

  return {
    dateString,
    timeString,
  };
};
