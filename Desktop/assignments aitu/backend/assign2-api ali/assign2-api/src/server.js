const express = require('express');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files
app.use(express.static('public'));

// API endpoints
app.get('/weather', async (req, res) => {
  try {
    const weatherData = await axios.get(
      `https://api.openweathermap.org/data/2.5/weather?q=${req.query.city}&appid=cf2871751847767e74d04dffa0576435`
    );
    res.json(weatherData.data);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Replace the /location endpoint with Google Maps Geocoding API
app.get('/location', async (req, res) => {
  try {
    const locationData = await axios.get(
      `https://maps.googleapis.com/maps/api/geocode/json?address=${req.query.city}&key=AIzaSyDFj3ayoSC7Jr07cyjAsWjIHepaz5mQ_ps`
    );

    const [latitude, longitude] = [
      locationData.data.results[0].geometry.location.lat,
      locationData.data.results[0].geometry.location.lng,
    ];

    res.json({
      lat: latitude,
      lon: longitude,
      place_name: locationData.data.results[0].formatted_address,
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});


app.get('/timezone', async (req, res) => {
  try {
    const timezoneData = await axios.get(
      `http://api.timezonedb.com/v2.1/get-time-zone?key=CVLYW38X5A9C&format=json&by=position&lat=${req.query.lat}&lng=${req.query.lon}`
    );
    res.json({ zoneName: timezoneData.data.zoneName });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
