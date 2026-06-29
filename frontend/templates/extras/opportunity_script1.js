let table;

$(document).ready(function(){

    /* ---------------------------
       DATATABLE INITIALIZATION
    --------------------------- */

    table = $('#opportunityTable').DataTable({

        pageLength: 5,

        lengthChange: false,

        info: false

    });

    /* ---------------------------
       CUSTOM SEARCH
    --------------------------- */

    $('#customSearch').on('keyup', function(){

        table.search(this.value).draw();

    });

    /* ---------------------------
       EXPORT BUTTON
    --------------------------- */

    $('#exportBtn').click(function(){

        alert('Export functionality will be connected later.');

    });

    /* ---------------------------
       ROW CLICK
    --------------------------- */

    $('#opportunityTable tbody').on('click', 'tr', function(){

        // remove previous selection

        $('#opportunityTable tbody tr')
            .removeClass('selected-row');

        // add new selection

        $(this).addClass('selected-row');

        // get row data

        let rowData = table.row(this).data();

        if(!rowData) return;

        let opportunity = rowData[0];
        let progress = rowData[1];
        let statusHtml = rowData[2];

        // Extract text from status pill

        let statusText = $('<div>')
            .html(statusHtml)
            .text()
            .trim();

        updateDetailsPanel(
            opportunity,
            progress,
            statusText
        );

    });

    /* ---------------------------
       VIEW BUTTON
    --------------------------- */

    $('#opportunityTable tbody').on(
        'click',
        '.view-btn',
        function(e){

            e.stopPropagation();

            let row = $(this).closest('tr');

            row.trigger('click');

        }
    );

    /* ---------------------------
       CLOSE DETAILS
    --------------------------- */

    $('#closeDetails').click(function(){

        $('#detailsPanel')
            .addClass('d-none');

        $('#opportunityTable tbody tr')
            .removeClass('selected-row');

    });

    /* ---------------------------
       KPI CARD ACTIVE STATE
    --------------------------- */

    $('.kpi-card').click(function(){

        $('.kpi-card')
            .removeClass('kpi-selected');

        $(this)
            .addClass('kpi-selected');

    });

});


/* =================================
   DETAILS PANEL UPDATE FUNCTION
================================= */

function updateDetailsPanel(
    opportunity,
    progress,
    status
){

    $('#detailsPanel')
        .removeClass('d-none');

    $('#detailTitle')
        .text(opportunity);

    let numericProgress =
        parseInt(progress);

    $('#detailProgress')
        .css(
            'width',
            numericProgress + '%'
        )
        .text(
            numericProgress + '%'
        );

    let statusBadge =
        $('#detailStatus');

    statusBadge
        .removeClass('active inactive');

    if(
        status.toLowerCase()
        === 'active'
    ){

        statusBadge
            .addClass('active');

    }
    else{

        statusBadge
            .addClass('inactive');

    }

    statusBadge.text(status);

    /* ---------------------------
       MOCK DATA FOR DEMO
    --------------------------- */

    let mockData = {

        "Bharti MPLS": {

            creator:
            "Rahul Sharma",

            date:
            "Jan 2024 - Dec 2025",

            customer:
            "Bharti",

            account:
            "MSO"

        },

        "FWA IP Core": {

            creator:
            "Priya Singh",

            date:
            "Apr 2024 - Mar 2026",

            customer:
            "Reliance",

            account:
            "Enterprise"

        },

        "Model-4V2": {

            creator:
            "Admin User",

            date:
            "Apr 2023 - Mar 2025",

            customer:
            "Bharti",

            account:
            "MSO"

        }

    };

    let details =
        mockData[opportunity];

    if(details){

        $('.detail-grid p')
            .eq(0)
            .text(details.creator);

        $('.detail-grid p')
            .eq(1)
            .text(details.date);

        $('.detail-grid p')
            .eq(2)
            .text(details.customer);

        $('.detail-grid p')
            .eq(3)
            .text(details.account);

    }

}


/* =================================
   OPTIONAL FILTER PLACEHOLDERS
================================= */

$('.form-select').change(function(){

    console.log(
        'Backend filter to be connected'
    );

});