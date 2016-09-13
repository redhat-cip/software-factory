// @licstart  The following is the entire license notice for the
// JavaScript code in this page.
//
// Copyright 2016 Red Hat
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.
//
// @licend  The above is the entire license notice
// for the JavaScript code in this page.

// Fancy tooltips
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});

angular.module('sfSettings', []).controller('mainController', function($scope, $http) {
    $scope.showSuccessAlert = false;
    $scope.showErrorAlert = false;
    $scope.successTextAlert = "";

    // Get user informations
    $http.get('/manage/services_users/?username='+localStorage.getItem("sf.username")).
        success(function(data) {
            $scope.user = data;
            // Remove un-managed data
            delete $scope.user.id;

            $scope.original = angular.copy($scope.user)
        }).
        error(function(data) {
            $scope.showErrorAlert = true;
        });

    // Get htpasswd status
    $http.get('/manage/htpasswd/')
        .success( function (data) {
          $scope.htpasswd_set = true;
          $scope.gerrit_api_key = "SECRET";
        })
        .error( function (data) {
          $scope.htpasswd_set = false;
          $scope.gerrit_api_key = "-";
        })
        .catch( function (data) {
          $scope.htpasswd_set = false;
          $scope.gerrit_api_key = "-";
        });

    // Get API token
    $http.get('/auth/apikey/?cauth_id='+localStorage.getItem("ls.id_token")).
        success(function(data) {
            $scope.sf_api_key = data.api_key
        }).
        error(function() {
            $http.post('/auth/apikey/?cauth_id='+localStorage.getItem("ls.id_token")).
                then(function(data) {
                    $scope.sf_api_key = data.api_key
                })
        });
    // Form submit action
    $scope.save = function() {
        if ($scope.original.idp_sync != $scope.user.idp_sync) {
            if (!$scope.user.idp_sync) {
                $scope.successTextAlert = "Identity Provider Sync is now disabled";
            } else {
                $scope.successTextAlert = "Identity Provider Sync is now enabled";
            }
        } else {
            $scope.successTextAlert = "";
        }
        // API takes fullname as full_name...
        $scope.user.full_name = $scope.user.fullname;
        $http.put('/manage/services_users/?username='+localStorage.getItem("sf.username"), $scope.user).
            success(function() {
                $scope.original = angular.copy($scope.user)
                $scope.showSuccessAlert = true;
            }).
            error(function() {
                $scope.user = angular.copy($scope.original);
                $scope.showErrorAlert = true;
            });
    };
    $scope.regen_api_key = function() {
            $http.delete('/auth/apikey/?cauth_id='+localStorage.getItem("ls.id_token")).
                then(function() {
                    $http.post('/auth/apikey/?cauth_id='+localStorage.getItem("ls.id_token")).
                        success(function(data) {
                            $scope.sf_api_key = data.api_key
                        })
                });
    };

    $scope.htpasswd_disable = function(name) {
        $scope.errors = false;
        $http.delete('/manage/htpasswd/')
            .success(function(data) {
                $scope.htpasswd_set = false;
                $scope.gerrit_api_key = "";
            })
            .error(function(data) {
                $scope.errors = data;
            });
    };

    $scope.htpasswd_enable = function(name) {
        $scope.errors = false;
        $http.put('/manage/htpasswd/')
            .success(function(data) {
                $scope.gerrit_api_key = data;
                $scope.htpasswd_set = true;
            })
            .error(function(data) {
                $scope.errors = data;
                $scope.htpasswd_set = false;
            });
    };

});
