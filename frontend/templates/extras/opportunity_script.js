let table;

$(document).ready(function () {
    console.log("JS LOADED");
    // Initialize DataTable
    table = $('#opportunityTable').DataTable();
    console.log(table);

    // Search box
    $('#customSearch').on('keyup', function () {
        table.search(this.value).draw();
    });

    // Filter chips
    $('.filter-chip').click(function () {

        $('.filter-chip').removeClass('active');
        $(this).addClass('active');

        let status = $(this).text().trim();

        if (status === "All") {
            table.column(2).search('').draw();
        }
        else {
            table.column(2).search(status).draw();
        }
    });

    // KPI Cards

    $('#onTrack').click(function(){

        $('.summary-card').removeClass('active-card');
        $(this).addClass('active-card');

        $('.filter-chip').removeClass('active');

        $('.filter-chip').filter(function(){
            return $(this).text().trim() === "On Track";
        }).addClass('active');

        table.search('On Track').draw();

    });

    $('#delayedCard').click(function(){

        $('.summary-card').removeClass('active-card');
        $(this).addClass('active-card');

        $('.filter-chip').removeClass('active');

        $('.filter-chip').filter(function(){
            return $(this).text().trim() === "Delayed";
        }).addClass('active');

        table.search('Delayed').draw();

    });

    // $('#pendingCard').click(function () {

    //     alert("Pending Updates page coming soon!");

    // });

    // $('#expiringCard').click(function () {

    //     alert("Expiring PO filter coming soon!");

    // });

    // Details Panel

    $('.view-btn').click(function () {

        $('#detailsPanel').removeClass('d-none');

        $('html, body').animate({
            scrollTop: $('#detailsPanel').offset().top
        }, 500);

    });

});

function setActiveCard(cardId){

    $('.summary-card')
        .removeClass('active-card');

    $(cardId)
        .addClass('active-card');
}

$('#delayedCard').click(function(){

    $('.summary-card').removeClass('active-card');
    $(this).addClass('active-card');

    $('.filter-chip').removeClass('active');

    $('.filter-chip').filter(function(){
        return $(this).text().trim() === 'Delayed';
    }).addClass('active');

    table.search('Delayed').draw();

});

$('#resetView').click(function(){

    $('.summary-card')
        .removeClass('hidden-card active-card');

    table.search('').columns().search('').draw();

});

$('.view-btn').click(function(){

    $('tr').removeClass('selected-row');

    $(this)
        .closest('tr')
        .addClass('selected-row');

});

$('#closeSummary').click(function(){

    $('#detailsPanel').addClass('d-none');

    $('tr').removeClass('selected-row');

});

$(document).click(function(e){

    if(
        !$(e.target).closest('#detailsPanel').length &&
        !$(e.target).closest('.view-btn').length
    ){

        $('#detailsPanel').addClass('d-none');

        $('tr').removeClass('selected-row');

    }

});
$('.filter-chip').click(function(){

    $('.filter-chip').removeClass('active');
    $(this).addClass('active');

    let status = $(this).text().trim();

    // reset KPI cards
    $('.summary-card').removeClass('active-card');

    if(status === "All"){

        table.search('').draw();

        return;
    }

    if(status === "On Track"){
        $('#onTrack').addClass('active-card');
    }

    if(status === "Delayed"){
        $('#delayedCard').addClass('active-card');
    }

    if(status === "Blocked"){
        $('#pendingCard').removeClass('active-card');
    }

    table.search(status).draw();

});

