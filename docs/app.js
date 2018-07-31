var app = angular.module('delegateApp', []);

app.filter('balance', function () {
    return function (value) {
        return Math.floor(value / 10000) / 100;
    }
});

app.controller('indexCtrl', function ($scope, $http, $filter) {
    $scope.classOfCycle = function (cycle, curcycle) {
        if (cycle < curcycle)
            return 'panel-green';
        else if (cycle == curcycle)
            return 'panel-yellow';
        else 
            return 'panel-red';
    };

    $scope.statusOfCycle = function (cycle, curcycle) {
        if (cycle < curcycle)
            return 'past' + (cycle > curcycle - 5 ? ' and frozen until cycle ' + (cycle + 5) : '');
        else if (cycle == curcycle)
            return 'current';
        else 
            return 'future';
    };

    $http.get('data.json').then(function (res) {
        $scope.data = res.data;
        $scope.lastcycle = res.data.cycles[res.data.cycles.length - 1];
        $scope.frozen = {};
        $scope.totalfrozen = 0;


        $scope.data.frozen.forEach (f => {
            $scope.frozen[f.cycle] = f;
            $scope.totalfrozen += parseInt (f.rewards);
        });

        setTimeout(function () {
            var generalchartdata = [];

            $scope.data.cycles.forEach(c => {
                generalchartdata.push({
                    cycle: c.cycle,
                    estimated_reward: $filter('balance')(c.rights.estimated_reward),
                    deleguees: c.snapshot.delegated.length,
                    stake: c.snapshot.staking_balance / 1000000000,
                    estimated_blocks: c.rights.blocks.length,
                    estimated_endorsment: c.rights.endorsment.length,
                    frozen: $filter('balance')(c.cycle in $scope.frozen ? $scope.frozen[c.cycle].rewards : 0),
                    reward: 0
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
                ykeys: ['estimated_reward', 'deleguees', 'stake', 'estimated_blocks', 'estimated_endorsment', 'frozen', 'reward'],
                labels: ['Estimated Reward', 'Deleguees', 'Stake', 'Estimated Blocks', 'Estimated Endorsment', 'Frozen', 'Reward'],
                pointSize: 2,
                hideHover: 'auto',
                resize: true,
                parseTime: false
            });

        }, 1000);
    });
});
