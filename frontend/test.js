// Simple test to verify Node.js server works
const express = require('express');

console.log('Testing if Express is available...');
console.log('Express version:', require('express/package.json').version);

const app = express();
app.get('/test', (req, res) => {
  res.json({ message: 'Frontend server is working!' });
});

const server = app.listen(3001, () => {
  console.log('✅ Test server running on port 3001');
  server.close();
  console.log('✅ Test completed successfully');
});