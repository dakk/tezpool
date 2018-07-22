var app = angular.module('delegateApp', []);

app.filter('balance', function () {
    return function (value) {
        return Math.floor(value / 10000) / 100;
    }
});

app.controller('indexCtrl', function ($scope, $http, $filter) {
    $scope.classOfCycleStatus = function (status) {
        switch (status) {
            case 'pending':
                return 'panel-yellow';
            case 'past':
                return 'panel-green';
            case 'future':
                return 'panel-red';
        }
    };

    $http.get('data.json').then(function (res) {
        $scope.data = res.data;
        $scope.lastcycle = res.data.cycles[res.data.cycles.length - 1];


        setTimeout(function () {
            var generalchartdata = [];

            $scope.data.cycles.forEach(c => {
                generalchartdata.push({
                    cycle: c.cycle,
                    estimated_reward: $filter('balance')(c.rights.estimated_reward),
                    deleguees: c.snapshot.delegated.length,
                    stake: c.snapshot.staking_balance / 1000000000,
                    estimated_blocks: c.rights.blocks.length,
                    estimated_endorsment: c.rights.endorsment.length
                });

                Morris.Donut({
                    element: 'chart-percentage-' + c.cycle,
                    data: c.snapshot.delegated.map(d => { return { label: d.alias, value: d.percentage } }),
                    formatter: function (value, data) { return value + '%'; },
                    resize: true
                });
            });

            Morris.Area({
                element: 'general-chart',
                data: generalchartdata,
                xkey: 'cycle',
                ykeys: ['estimated_reward', 'deleguees', 'stake', 'estimated_blocks', 'estimated_endorsment'],
                labels: ['Estimated Reward', 'Deleguees', 'Stake', 'Estimated Blocks', 'Estimated Endorsment'],
                pointSize: 2,
                hideHover: 'auto',
                resize: true,
                parseTime: false
            });

        }, 1000);
    });
});
