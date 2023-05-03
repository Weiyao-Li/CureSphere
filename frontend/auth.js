AWS.config.region = config.Region;
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
  IdentityPoolId: 'YOUR_IDENTITY_POOL_ID'
});

var cognitoUser = null;

function signIn() {
  var email = document.getElementById('email').value;
  var password = document.getElementById('password').value;

  var authenticationData = {
    Username: email,
    Password: password,
  };

  var authenticationDetails = new AWS.CognitoIdentityServiceProvider.AuthenticationDetails(authenticationData);
  var userPool = new AWS.CognitoIdentityServiceProvider.CognitoUserPool(poolData);
  var userData = {
    Username: email,
    Pool: userPool,
  };
  cognitoUser = new AWS.CognitoIdentityServiceProvider.CognitoUser(userData);

  cognitoUser.authenticateUser(authenticationDetails, {
    onSuccess: function (result) {
      // (success handler code)
    },
    onFailure: function (err) {
      alert(err.message || JSON.stringify(err));
    },
  });
}

function signUp() {
  var email = document.getElementById('email').value;
  var password = document.getElementById('password').value;
  var userType = document.getElementById('userType').value;

  var userPool = new AWS.CognitoIdentityServiceProvider.CognitoUserPool(poolData);

  var attributeList = [];

  var dataUserType = {
    Name: 'custom:user_type', // Replace 'user_type' with the name of your custom attribute in Cognito
    Value: userType
  };

  var attributeUserType = new AWS.CognitoIdentityServiceProvider.CognitoUserAttribute(dataUserType);
  attributeList.push(attributeUserType);

  userPool.signUp(email, password, attributeList, null, function (err, result) {
    if (err) {
      alert(err.message || JSON.stringify(err));
      return;
    }
    cognitoUser = result.user;
    alert('User registered successfully. Please check your email for verification.');
  });

}
// // Create a configuration object for the SDK
// var config = {
//   UserPoolId: 'us-east-1_rcOSgHhwK',
//   ClientId: '6q648n1e0kgnsbpiijj23hrb6',
//   Region: 'us-east-1',
// };
//
// AWS.config.region = config.Region;
// AWS.config.credentials = new AWS.CognitoIdentityCredentials({
//   IdentityPoolId: 'YOUR_IDENTITY_POOL_ID'
// });
//
// var cognitoUser = null;
//
// var poolData = {
//   UserPoolId: config.UserPoolId,
//   ClientId: config.ClientId
// };
//
// function signIn() {
//   var email = document.getElementById('email').value;
//   var password = document.getElementById('password').value;
//
//   var authenticationData = {
//     Username: email,
//     Password: password,
//   };
//
//   var authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
//   var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
//   var userData = {
//     Username: email,
//     Pool: userPool,
//   };
//   cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
//
//   cognitoUser.authenticateUser(authenticationDetails, {
//     onSuccess: function (result) {
//       var accessToken = result.getAccessToken().getJwtToken();
//       var idToken = result.getIdToken().getJwtToken();
//
//       var groups = result.idToken.payload['cognito:groups'];
//
//       if (groups.includes('doctor')) {
//         alert('User is a Doctor. Login successful.');
//         window.location.href = 'index.html';
//       } else if (groups.includes('patient')) {
//         alert('User is a Patient. Login successful.');
//         window.location.href = 'index.html';
//       } else {
//         alert('Unrecognized user type');
//       }
//     },
//     onFailure: function (err) {
//       alert(err.message || JSON.stringify(err));
//     },
//   });
// }
//
// function signUp() {
//   var email = document.getElementById('email').value;
//   var password = document.getElementById('password').value;
//
//   var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
//
//   userPool.signUp(email, password, [], null, function (err, result) {
//     if (err) {
//       alert(err.message || JSON.stringify(err));
//       return;
//     }
//     cognitoUser = result.user;
//     alert('User registered successfully. Please check your email for verification.');
//   });
// }
