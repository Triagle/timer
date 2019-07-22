async function getEntryData() {
    let response = await fetch('/entries');
    let data = await response.json();
    return data;
}

function genGraph() {
    getEntryData().then(entries => {
        var ctx = document.getElementById("chart").getContext('2d');
        projects = {};
        colours = {};
        for (entry of entries) {
            if (entry.duration == null) {
                continue;
            }
            if (entry.project == null) {
                if (projects['No Project'] == undefined) {
                    projects['No Project'] = 0;
                }
                projects['No Project'] += entry.duration;
                colours['No Project'] = 'rgb(224, 224, 224, 1)'
            } else {
                if (projects[entry.project.name] == undefined) {
                    projects[entry.project.name] = 0;
                }
                projects[entry.project.name] += entry.duration;
                colours[entry.project.name] = entry.project.colour;
            }
        }
        projectNames = Object.keys(projects)
        projectNames.sort();
        projectDurations = projectNames.map(name => projects[name])
        colourValues = projectNames.map(name => colours[name]);
        let data = {
            labels: Object.keys(projects),
            datasets: [{
                fill: true,
                backgroundColor: Object.values(colours),
                data: Object.values(projects)
            }]
        };
        var chart = new Chart(ctx, {
            type: "pie",
            data: data,
            options: {
                tooltips: {
                    callbacks: {
                        label: (tooltipItem, data) => {
                            let seconds = data.datasets[0].data[tooltipItem.index];
                            let hours = Math.floor(seconds / 3600);
                            let minutes = Math.floor((seconds % 3600) / 60);
                            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
                        }
                    }
                }
            }
        })
    })
}
function postData(url = '', data = {}) {
    // Default options are marked with *
    return fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE, etc.
        mode: 'cors', // no-cors, cors, *same-origin
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: {
            'Content-Type': 'application/json',
            // 'Content-Type': 'application/x-www-form-urlencoded',
        },
        redirect: 'follow', // manual, *follow, error
        referrer: 'no-referrer', // no-referrer, *client
        body: JSON.stringify(data), // body data type must match "Content-Type" header
    })
        .then(response => response.json()); // parses JSON response into native JavaScript objects 
}

function addEntry(event) {
    event.preventDefault();
    let add = document.getElementById('entryInput');
    postData('/add', {data: add.value}).then(_ => location.reload());
}

function utcISO(date) {
    return `${date.getUTCFullYear()}-${(date.getUTCMonth() + 1).toString().padStart(2, '0')}-${date.getUTCDate().toString().padStart(2, '0')}`
}

window.addEventListener('load', function () {
    genGraph();
    let form = document.getElementById('entryForm');
    let today_url = document.getElementById('today-url');
    var midnight = new Date();
    midnight.setHours(0, 0, 0, 0);
    today_url.href = `/?after=${utcISO(midnight)}&period=today`
    midnight.setHours(0, 0, 0, 0);
    form.addEventListener('submit', addEntry);
    Array.from(document.getElementsByClassName('delete-button')).forEach((delLink) => {
        delLink.addEventListener('click', (event) => {
            event.preventDefault();
            let id = delLink.getAttribute('entry-id');
            fetch(`/delete/${id}`, {
                method: 'DELETE', // *GET, POST, PUT, DELETE, etc.
                mode: 'cors', // no-cors, cors, *same-origin
                cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
                credentials: 'same-origin', // include, *same-origin, omit
                headers: {},
                redirect: 'follow', // manual, *follow, error
                referrer: 'no-referrer', // no-referrer, *client
            }).then(() => window.location.reload())
        })
    })
    Array.from(document.getElementsByClassName('stop-button')).forEach((button) => {
        button.addEventListener('click', (event) => {
            let id = event.target.getAttribute('entry-id');
            postData('/stop', {id: id})
        })
    })
})

