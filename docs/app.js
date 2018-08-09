var app = angular.module('delegateApp', []);

app.filter('balance', function () {
    return function (value) {
        let vv = Math.floor(value / 10000) / 100;
        if (isNaN (vv))
            return 0.0;
        return vv;
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
        if ((cycle - 1) < curcycle)
            return 'past' + (cycle > curcycle - 5 ? ' and frozen until cycle ' + (cycle + 5) : '');
        else if (cycle == curcycle)
            return 'current';
        else 
            return 'future';
    };

    $http.get('paylog.json').then(function (res) {
        $scope.paylog = res.data;
    });

    $http.get('data.json').then(function (res) {
        $scope.data = res.data;
        $scope.lastcycle = res.data.cycles[res.data.cycles.length - 1];

        setTimeout(function () {
            var generalchartdata = [];

            $scope.data.cycles.forEach(c => {
                var d = {
                    cycle: c.cycle,
                    estimated_reward: $filter('balance')(c.rights.estimated_reward),
                    deleguees: c.snapshot.delegated.length,
                    stake: c.snapshot.staking_balance / 1000000000,
                    estimated_blocks: c.rights.blocks.length,
                    estimated_endorsment: c.rights.endorsment.length
                };

                if ($scope.paylog && c.cycle in $scope.paylog['cycles']) {
                    d.reward = $filter('balance')($scope.paylog['cycles'][c.cycle]['reward']);
                    d.frozen = $filter('balance')($scope.paylog['cycles'][c.cycle]['frozen']);
                } else {
                    d.reward = 0;
                    d.frozen = 0;
                }

                generalchartdata.push(d);

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
                ykeys: ['estimated_reward', 'deleguees', 'stake', 'estimated_blocks', 'estimated_endorsment', 'reward', 'frozen'],
                labels: ['Estimated Reward', 'Deleguees', 'Stake', 'Estimated Blocks', 'Estimated Endorsment', 'Reward', 'Frozen'],
                pointSize: 2,
                hideHover: 'auto',
                resize: true,
                parseTime: false
            });

        }, 1000);
    });
});
