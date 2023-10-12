document.addEventListener("DOMContentLoaded", function() {

//Selects all input fields
var theuser_name = document.getElementById("createusername");
var thepassword_og = document.getElementById("createpassword");
var thepassword_conf = document.getElementById("confirmpassword");

//Selects all spaces below input fields to display messages
var user_message = document.getElementById("usermessage");
var ogpassmsg = document.getElementById("passwordmessage1");
var confpassmsg = document.getElementById("passwordmessage2");

//Selects the value of the input fields
var user_name = theuser_name.value;
var password1 = thepassword_og.value;
var password2 = thepassword_conf.value;

//Select register button
const thebutton = document.getElementById("registered");

var has_alpha = false;
var has_number = false;
var has_lower = false;
var has_upper = false;
var has_length = false;

//Disable register button initially
thebutton.disabled = true;

    function check_password(string) {

        for (let i = 0; i < string.length; i++) {
            //Checks if password contains at least one letter
            if (isNaN(string[i])) {
                has_alpha = true;
                break;
            }
        }

        for (let j = 0; j < string.length; j++) {
            //Checks if password contains at least one upper letter
            if (string[j] === string[j].toUpperCase()) {
                has_upper = true;
                break;
            }
        }

        for (let k = 0; k < string.length; k++) {
            //Checks if password contains at least one lowercase letter
            if (string[k] === string[k].toLowerCase()) {
                has_lower = true;
                break;
            }
        }

        for (let l = 0; l < string.length; l++) {
            //Checks if password contains at least one number
            if (!isNaN(string[l])) {
                has_number = true;
                break;
            }
        }

        for (let m = 0; m < string.length; m++)
        {
            if (m >= 9) {
                has_length = true;
                break;
            }
        }

        if (has_alpha && has_number && has_upper && has_lower && has_length)
        {
            return true;
        }
        else {
            return false;
        }
    };

    function check_match(string1, string2) {
        if (string1 != string2) {
            return false;
        }
        else {
            return true;
        }
    }

    function check_username(username) {
        is_length = false;
        //Ensures username is at least 8 characters
        if (username.length >= 8) {
            is_length = true;
        }
        return is_length;
    };

    thepassword_og.addEventListener("keyup", function() {

        has_alpha = false;
        has_number = false;
        has_lower = false;
        has_upper = false;
        has_length = false;

        password1 = thepassword_og.value;

        successful_reg();

        if(check_password(password1)) {
            ogpassmsg.innerHTML = "";
        }
        else {
            ogpassmsg.innerHTML = "Password must contain one uppercase letter, one lowercase letter, one number and be at least 10 characters.";
        }
    });

    thepassword_conf.addEventListener("keyup", function () {

        password2 = thepassword_conf.value;

        successful_reg();

        if (!check_match(password1, password2)) {
            confpassmsg.innerHTML = "Passwords do not match.";
        }
        else {
            confpassmsg.innerHTML = "";
        }
    });

    theuser_name.addEventListener("keyup", function() {

        user_name = theuser_name.value;

        successful_reg();

        if (!check_username(user_name)) {
            user_message.innerHTML = "Username must be at least 8 characters.";
        }
        else {
            user_message.innerHTML = "";
        }
    });

    function successful_reg() {
        let can_register = false;

        if (check_password(password1) && check_match(password1, password2) && check_username(user_name)) {
            can_register = true;
        }
        else {
            can_register = false;
        }

        if (can_register) {
            thebutton.disabled = false;
        }
        else {
            thebutton.disabled = true;
        }
    };
});