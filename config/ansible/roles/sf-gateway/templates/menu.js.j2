
function isCookiesEnabled() {
    var isEnabled = (navigator.cookieEnabled) ? true : false;
    if ( typeof navigator.cookieEnabled == "undefined" && !cookieEnabled ) {
        document.cookie='test';
        isEnabled = (document.cookie.indexOf('test')!=1) ? true : false;
    }
    return isEnabled;
}

function getValueOfKey(target, key) {
    var tokens = target.split(/%3B/); // semi-colon
    for ( var i = 0; i < tokens.length; i++ ) {
        var keyvalue = tokens[i].split(/%3D/);
        if ( key.indexOf(keyvalue[0]) == 0 ) {
            return keyvalue[1];
        }
    }
    return false;
}

function displayLoggedIn(username) {
    try {
        document.getElementById("login-msg").innerHTML = "Welcome " + username;
        document.getElementById("login-msg").style.display = "block";
        document.getElementById("login-btn").style.display = "none";
        document.getElementById("login-setting").style.display = "block";
        document.getElementById("logout-btn").style.display = "block";
    } catch (err) {
    }
}

function displaySignIn() {
    try {
        localStorage.removeItem("ls.access_token");
        localStorage.removeItem("ls.token_type");
        localStorage.removeItem("ls.id_token");
        document.getElementById("login-msg").innerText = "";
        document.getElementById("login-msg").style.display = "none";
        document.getElementById("login-btn").style.display = "block";
        document.getElementById("login-setting").style.display = "none";
        document.getElementById("logout-btn").style.display = "none";
    } catch (err) {
    }
}

function initAuth() {
    if ( isCookiesEnabled() ) {
        var tokens = document.cookie.split(';');
        for ( var i = 0; i < tokens.length; i++ ) {
            tokens[i] = tokens[i].trim();
            if ( tokens[i].indexOf('auth_pubtkt') == 0 ) {
                var username = getValueOfKey(tokens[i].substring(12), 'uid');
                if ( username ) {
                    // cid is the cauth_id that is equal to the storyboard user id
                    var storyboard_user_id = getValueOfKey(tokens[i].substring(12), 'cid')
                    localStorage.setItem("ls.id_token", storyboard_user_id);
                    // storyboard_api is already protected by cauth, the token is the username
                    localStorage.setItem("ls.access_token", username);
                    localStorage.setItem("ls.token_type", "Bearer");
                    // store sf user info
                    localStorage.setItem("sf.username", username);
                    displayLoggedIn(username);
                    return;
                }
            }
        }
    }
    displaySignIn();
};

/** Init function
 */
if (document.body) {
    initAuth();
} else {
    document.onload = function() {initAuth();};
}
