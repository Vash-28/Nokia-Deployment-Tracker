const toggleBtn = document.getElementById('togglePassword');
const password = document.getElementById('password');

toggleBtn.addEventListener('click', function(){
    const icon = this.querySelector('i');

    if(password.type === 'password'){
        password.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        password.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
});

document.getElementById("loginForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const pwd = password.value;

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: pwd })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.href = "/dashboard";
        } else {
            alert(data.message);
        }
    });
});