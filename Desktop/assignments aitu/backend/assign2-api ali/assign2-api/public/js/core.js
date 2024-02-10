// Function to fetch weather data from OpenWeatherAPI
async function getWeather(city) {
  try {
    const response = await fetch(`/weather?city=${city}&apiKey=cf2871751847767e74d04dffa0576435`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching weather data:', error);
    return null;
  }
}

// Function to fetch location data from Nominatim (OpenStreetMap) API
async function getLocation(city) {
  try {
    const response = await fetch(`/location?city=${city}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching location data:', error);
    return null;
  }
}

// Function to fetch timezone data from TimeZoneDB API
async function getTimezone(lat, lon) {
  try {
    const response = await fetch(`/timezone?lat=${lat}&lon=${lon}&apiKey=CVLYW38X5A9C`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching timezone data:', error);
    return null;
  }
}

async function updateUI(city, latitude, longitude) {
  const weatherData = await getWeather(city);
  const timezoneData = await getTimezone(latitude, longitude);

  // Convert temperature from Kelvin to Celsius
  const temperatureCelsius = (weatherData.main.temp - 273.15).toFixed(2);

  // Get local time based on timezone
  const localTime = new Date().toLocaleString('en-US', {
    timeZone: timezoneData.zoneName,
  });

  // Update the UI elements
  document.getElementById('weather').textContent = `Weather: ${weatherData.weather[0].description}`;
  document.getElementById('temperature').textContent = `Temperature: ${temperatureCelsius}°C`;
  document.getElementById('location').textContent = `Location: ${city}`;
  document.getElementById('timezone').textContent = `Local Time: ${localTime}`;

  // Initialize and display the map using Google Maps API
  initMap(latitude, longitude);
}

// Function to initialize the map using Google Maps API
function initMap(lat, lon) {
  const mapOptions = {
    center: { lat, lng: lon },
    zoom: 13,
  };
  const map = new google.maps.Map(document.getElementById('map'), mapOptions);

  const marker = new google.maps.Marker({
    position: { lat, lng: lon },
    map: map,
  });
}

// Event listener for the form submission
document.getElementById('cityForm').addEventListener('submit', async function (event) {
  event.preventDefault();
  const city = document.getElementById('cityInput').value;

  // Fetch both weather and timezone data concurrently
  const [weatherData, locationData] = await Promise.all([
    getWeather(city),
    getLocation(city),
  ]);

  // Get local time based on timezone
  const timezoneData = await getTimezone(locationData.lat, locationData.lon);
  const temperatureCelsius = (weatherData.main.temp - 273.15).toFixed(2);

  // Get local time based on timezone
  const localTime = new Date().toLocaleString('en-US', {
    timeZone: timezoneData.zoneName,
  });

  // Update the UI elements
  document.getElementById('weather').textContent = `Weather: ${weatherData.weather[0].description}`;
  document.getElementById('temperature').textContent = `Temperature: ${temperatureCelsius}°C`;
  document.getElementById('location').textContent = `Location: ${city}`;
  document.getElementById('timezone').textContent = `Local Time: ${localTime}`;

  // Initialize and display the map using Google Maps API
  initMap(locationData.lat, locationData.lon);
});