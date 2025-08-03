document.getElementById('auth-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent form submission
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    // Here you would typically call an API to authenticate the user
    console.log(`Username: ${username}, Password: ${password}`); // Mock authentication
});