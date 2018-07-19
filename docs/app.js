var app = angular.module('delegateApp', []);

app.controller('indexCtrl', function($scope, $http) {

    $http.get ('paydb.json').then (function (res) {
    });
});
