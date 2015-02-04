
var extraObstacle = 
    "<div id='obstacle'>" +
    "   <br />" +
    "   <fieldset>" +
    "       <legend>Obstacles</legend>" +
    "       <label> x:<input type='text' name='x' size='30' maxlength='100'></label>" +
    "       <br />" +
    "       <label>y:<input type='text' name='y' size='30' maxlength='100'></label>" +
    "       <br />" +
    "       <label>w:<input  type='text' name='w' size='30' maxlength='100'></label>" +
    "       <br />" +
    "       <label>h:<input type='text' name='h' size='30' maxlength='100'></label>" +
    "       <br />" +
    "   </fieldset>" +
    "</div>";

function addObstacle() {
    $('#obstacles').append(extraObstacle);
};

function addWaypoint() {
    var data = {
        x: $('#waypoint [name="x"]').val(),
        y: $('#waypoint [name="y"]').val()
    };

    $.ajax({
        url: '/waypoint',
        type: 'POST',
        data: data,
    }).success(function(data) {
        $('#waypoint [name="x"]').val("");
        $('#waypoint [name="y"]').val("");
        $.ajax({
            url: '/waypoint',
            type: 'GET'
        }).success(function(data) {
            $('#waypoints-list').html(JSON.stringify(data.waypoints));
        }).error(function(data) {
            console.log("Could not get waypoints");
        });
    }).error(function(data) {
        console.log("error:", data);
    });
};

function submitSetUp() {
    var data = {
        start: [$('#start-x').val(), $('#start-y').val()],
        width: $('[name="width"]').val(),
        height: $('[name="height"]').val(),
        obstacles: []
    };

    $("#obstacles fieldset").each(function(i, e) {
        e = $(e);
        var x = e.find('[name="x"]').val();
        var y = e.find('[name="y"]').val();
        var w = e.find('[name="w"]').val();
        var h = e.find('[name="h"]').val();
        data.obstacles.push([x, y, w, h]);
    });

    $.ajax({
        url: '/setup',
        type: 'POST',
        data: data,
    }).success(function(data) {
        console.log("success:", data);
        window.location = '/2';
    }).error(function(data) {
        console.log("error:", data);
    });
}

function start() {
    $.ajax({
        url: '/start',
        type: 'POST'
    }).success(function(data) {
        console.log("Car started!", data);
    }).error(function(data) {
        console.log("Error could not start car:", data);
    });
}

function stop() {
    $.ajax({
        url: '/stop',
        type: 'POST'
    }).success(function(data) {
        console.log("Car stopped!", data);
    }).error(function(data) {
        console.log("Error could not stop car:", data);
    });
};

function deleteWaypoints() {
    $.ajax({
        url: '/waypoint', 
        type: 'DELETE'
    }).success(function(data) {
        console.log("Waypoints deleted:", data);
        $('#waypoints-list').html("");
    }).error(function(data) {
        console.log("Error could not delete waypoints:", data);
    });
};

function submitRedefine() {
    $.ajax({
        url: '/stop',
        type: 'POST'
    }).success(function(data) {
        console.log("Car stopped!", data);
        window.location = '/';
    }).error(function(data) {
        console.log("Error could not stop car:", data);
    });
};