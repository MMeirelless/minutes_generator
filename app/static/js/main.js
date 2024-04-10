// Functions
async function postRequest(endpoint, payload){
    return fetch(endpoint, {
        method: "POST",
        cache: "no-cache",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
        },
        redirect: "follow",
        referrerPolicy: "no-referrer",
        body: JSON.stringify(payload),
    })
} 

document.addEventListener("DOMContentLoaded", function(){ 
    // My Account
    if (document.getElementById("my_account")){
        const saveAccountBtn = document.getElementById('saveAccountBtn')
        const editProfileModal = document.getElementById('editProfileModal');

        async function deleteAccount() {
            Swal.fire({
                title: 'Tem certeza?',
                text: "Você não poderá reverter isso!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sim, deletar!'
            }).then((result) => {
                if (result.isConfirmed) {

                    const response = postRequest("/delete_account", {})
                    Swal.fire(
                        'Deletado!',
                        'Sua conta foi deletada.',
                        'success'
                    ).then((result) => {
                        if (result.isConfirmed) {
                            location.href="/logout"
                            return response.json();
                        }
                    })
                }
            })
        }
        async function enable2FA() {
            Swal.fire({
                title: 'Ativar Verificação de Dois Fatores?',
                text: "Você não poderá reverter isso!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sim, ativar!'
            }).then((result) => {
                if (result.isConfirmed) {
                    location.href="/setup_2fa"
                }
            })
        }
        async function saveAccount() {
            var payload = {
                "username": document.getElementById('username').value,
                "email": document.getElementById('email').value,
                "code": document.getElementById('code').value,
                "pwd_old": document.getElementById('pwd_old').value,
                "pwd_new": document.getElementById('pwd_new').value,
            };

            await postRequest("/update_account", payload)
            .then(response => response.json())
            .then(data => {
                if(data["response"]=="success" || data["response"]=="error"){
                    location.href = "/my_account"
                    saveAccountBtn.classList.remove('btn-disabled')
                }
                else if(data["response"]=="wrong_pwd"){
                    document.getElementById("password-message").style.display = "block"
                    saveAccountBtn.classList.remove('btn-disabled')
                }
                else if (data["response"]=="changing_email"){
                    document.getElementById("code-container").style.display = "block"
                    saveAccountBtn.classList.remove('btn-disabled')
                }
                else if (data["response"]=="wrong_code"){
                    document.getElementById("code-message").innerText = "Código errado."
                    saveAccountBtn.classList.remove('btn-disabled')
                }
            })
        }

        editProfileModal.addEventListener('hidden.bs.modal', function () {
            document.getElementById("password-message").style.display = "none"
            document.querySelector('#editProfileModal .modal-body form').reset();
            document.getElementById("code-container").style.display = "none";
            document.getElementById("code-message").innerText = 'Enviamos um código para o seu e-mail. Entre ele aqui e clique em "Salvar Alterações" novamente.';
            postRequest("/reset_code", {});
        });

        saveAccountBtn.addEventListener('click', function(){
            this.classList.add('btn-disabled')
            saveAccount()
        })
        document.getElementById('deleteAccountBtn').addEventListener('click', function(){
            deleteAccount()
        })

        document.getElementById('2faBtn').addEventListener('click', function(){
            enable2FA()
        })

        // License Time Chart
        var ctx = document.getElementById('licencaUsageChart').getContext('2d');
        var licencaUsageChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho'],
                datasets: [{
                    label: 'Minutos Utilizados',
                    data: [50, 75, 150, 100, 200, 175],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    datalabels: {
                        align: 'end',
                        anchor: 'end',
                        backgroundColor: function(context) {
                            return context.dataset.borderColor;
                        },
                        borderRadius: 4,
                        color: 'white',
                        formatter: Math.round
                    }
                }
            },
            plugins: [ChartDataLabels]
        });

        // Recomendation
        var totalUsage = licencaUsageChart.data.datasets[0].data.reduce((a, b) => a + b, 0);
        var averageUsage = totalUsage / licencaUsageChart.data.datasets[0].data.length;
        var recommendation = document.getElementById('licencaRecommendation');

        if (averageUsage > 180) {
            recommendation.innerText = 'Recomendamos contratar um plano melhor devido ao alto consumo.';
        } else if (averageUsage < 100) {
            recommendation.innerText = 'Seu consumo atual está baixo, talvez um plano mais simples atenda suas necessidades.';
        } else {
            recommendation.innerText = 'Seu plano atual parece adequado ao seu consumo.';
        }
    }
    // My Reports
    if (document.getElementById("my_reports")){
        const deleteButton = document.querySelectorAll(".btn-delete")
    
        if(deleteButton){
            deleteButton.forEach(function(button){
                button.addEventListener("click", function(){
                    Swal.fire({
                    title: 'Apagar Relatório?',
                    text: 'Seu relatório será movido para a lixeira e permanecerá em nosso Banco de Dados por 7 dias. Tem certeza que deseja executar essa ação?',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    cancelButtonColor: '#d33',
                    confirmButtonText: 'Prosseguir',
                    cancelButtonText: 'Cancelar'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            postRequest("/delete_report", {"report_id":this.dataset.id})                            
                            setTimeout(function(){location.href = "/my_reports"}, 100)
                        }
                    });
                })
            })
        }
    }
    // New Report
    if (document.getElementById("new_report")){
        const downloadButton = document.querySelector('.btn-download');
        const newReportButton = document.querySelector('.btn-new');
        const saveButton = document.querySelector('.btn-save');
        const generateButton = document.querySelector(".btn-generate");
        const generateForm = document.querySelector("#audio_upload_form");
        const reportLoader = document.querySelector(".report-loader");

        if (is_report_generated) {
            generateForm.style.display = "none"
        }

        if(generateButton) {
            generateButton.addEventListener('click', function() {
                generateForm.style.display = "none"
                reportLoader.style.display = "block"
            })
        }

        if (downloadButton) {
        downloadButton.addEventListener('click', function() {
            
            this.classList.add('btn-disabled');
            
            Swal.fire({
                title: 'Download iniciado!',
                text: 'Seu download foi iniciado. Por favor, verifique sua pasta de downloads.',
                icon: 'success',
                confirmButtonColor: '#3085d6',
                confirmButtonText: 'OK',
            }).then((result) => {
                if (result.isConfirmed) {
                    
                }
            });
        });
    }

        if (newReportButton) {
            newReportButton.addEventListener('click', function(e) {
                e.preventDefault();
                Swal.fire({
                    title: 'Tem certeza?',
                    text: "Você está prestes a criar um novo relatório. Certifique-se de ter salvo ou baixado o relatório atual. O relatório atual será apagado.",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    cancelButtonColor: '#d33',
                    confirmButtonText: 'Prosseguir',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = '/new_report';
                    }
                });
            });
        }

        // Salvar Relatório
        if (saveButton) {
            saveButton.addEventListener('click', function(e) {
                e.preventDefault();
                Swal.fire({
                    title: 'Você deseja salvar o relatório?',
                    text: "Não recomendamos salvar informações sensíveis.",
                    icon: 'info',
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    cancelButtonColor: '#d33',
                    confirmButtonText: 'Salvar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        var reportClone = document.querySelector('.report').cloneNode(true);

                        reportClone.querySelectorAll('a').forEach(function(a) {
                            a.remove();
                        });

                        var payload = {"html_content":reportClone.outerHTML,"html_content_title":html_content_title};
                        
                        async function saveReport() {
                            const response = await postRequest("/save_report", payload)
                            return response.json();
                        }

                        saveReport()

                        document.querySelector(".btn-save").classList.add('btn-disabled')
                    }
                });
            });
        }
    }
    // Trash
    if (document.getElementById("trash")){
        const deleteButton = document.querySelectorAll(".btn-delete")
    
        if(deleteButton){
            deleteButton.forEach(function(button){
                button.addEventListener("click", function(){
                    Swal.fire({
                    title: 'Apagar Relatório?',
                    text: 'Seu relatório será movido para a lixeira e permanecerá em nosso Banco de Dados por 7 dias. Tem certeza que deseja executar essa ação?',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    cancelButtonColor: '#d33',
                    confirmButtonText: 'Prosseguir',
                    cancelButtonText: 'Cancelar'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            postRequest("/delete_trash", {"report_id":this.dataset.id})                            
                            setTimeout(function(){location.href = "/trash"}, 100)
                        }
                    });
                })
            })
        }
    }

    // Register
    if (document.getElementById("register")){
        function openPicModal() {
            $('#picModal').modal('show');
        }
        
        function selectPic(picName, element) {
            if (picName !== '') {
                document.getElementById('selectedImagePreview').src = "{{ url_for('static', filename='images/user_pictures/') }}" + picName;
                document.getElementById('selectedPic').value = picName;
                $('#picModal').modal('hide');
            }
        }

        document.querySelector("#user-pic").addEventListener("click", function(){
            openPicModal()
        })
        document.querySelector("#user-pic").addEventListener("click", function(){
            openPicModal()
        })
    }
})