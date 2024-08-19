document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('dreamForm');
    form.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent the default form submission

        // Submit the form using JavaScript
        fetch(form.action, {
            method: form.method,
            body: new FormData(form),
        }).then(response => response.text()).then(html => {
            // Parse the new HTML response
            var parser = new DOMParser();
            var doc = parser.parseFromString(html, 'text/html');
            
            // Replace the current content with the new content
            document.body.innerHTML = doc.body.innerHTML;
            
            // Clear the form
            form.reset();
        }).catch(error => console.error('Error:', error));
    });
});
