var checkout = {};

$(document).ready(function() {
  var $messages = $('.messages-content'),
    d, h, m,
    i = 0;

  $(window).load(function() {
    $messages.mCustomScrollbar();
    insertResponseMessage('Hi there, I\'m your CureSphere personal AI assistant. How can I help?');
  });

  function updateScrollbar() {
    $messages.mCustomScrollbar("update").mCustomScrollbar('scrollTo', 'bottom', {
      scrollInertia: 10,
      timeout: 0
    });
  }

  function setDate() {
    d = new Date()
    if (m != d.getMinutes()) {
      m = d.getMinutes();
      $('<div class="timestamp">' + d.getHours() + ':' + m + '</div>').appendTo($('.message:last'));
    }
  }

  function callChatbotApi(message) {
    // params, body, additionalParams
    return sdk.chatbotPost({}, {
      messages: [{
        type: 'unstructured',
        unstructured: {
          text: message
        }
      }]
    }, {headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        }});
  }


  function handleFulfilledIntent() {
  window.location.href = "../displayDoctor.html";
}

  function insertMessage() {
  msg = $('.message-input').val();
  if ($.trim(msg) == '') {
    return false;
  }
  $('<div class="message message-personal">' + msg + '</div>').appendTo($('.mCSB_container')).addClass('new');
  setDate();
  $('.message-input').val(null);
  updateScrollbar();

  callChatbotApi(msg)
    .then((response) => {
      console.log(response.data);

      var data = response.data;
      const sessionState = data.messages[0].unstructured.text.sessionState;
      const intentState = sessionState.intent.state;

      if (intentState === "Fulfilled") {

        // save data to local storage
        localStorage.setItem('doctorData', JSON.stringify(data.messages[0].unstructured.text.messages[0].content));

        handleFulfilledIntent();
      } else {
        if (data.messages && data.messages.length > 0) {
          console.log('received ' + data.messages.length + ' messages');
          console.log('data.messages content:', JSON.stringify(data.messages, null, 2));

          const messages = data.messages[0].unstructured.text.messages;
          const textContent = messages[0].content;

          insertResponseMessage(textContent);
        } else {
          insertResponseMessage('Oops, something went wrong. Please try again.');
        }
      }
    })
    .catch((error) => {
      console.log('an error occurred', error);
      insertResponseMessage('Oops, something went wrong. Please try again.');
    });
}



//   function insertMessage() {
//   msg = $('.message-input').val();
//   if ($.trim(msg) == '') {
//     return false;
//   }
//   $('<div class="message message-personal">' + msg + '</div>').appendTo($('.mCSB_container')).addClass('new');
//   setDate();
//   $('.message-input').val(null);
//   updateScrollbar();
//
//   callChatbotApi(msg)
//     .then((response) => {
//       console.log(response.data);
//
//       var data = response.data;
//       if (data.interpretations && data.interpretations.length > 0) {
//         var intentState = data.interpretations[0].intent.state;
//       }
//       if (intentState === "Fulfilled") {
//         handleFulfilledIntent();
//       } else {
//         if (data.messages && data.messages.length > 0) {
//           console.log('received ' + data.messages.length + ' messages');
//           console.log('data.messages content:', JSON.stringify(data.messages, null, 2));
//
//           const messages = data.messages[0].unstructured.text.messages;
//           const textContent = messages[0].content;
//
//           for (var message of textContent) {
//             if (message.type === 'unstructured') {
//               insertResponseMessage(message.unstructured.text);
//             } else if (message.type === 'structured' && message.structured.type === 'product') {
//               var html = '';
//
//               insertResponseMessage(message.structured.text);
//
//               setTimeout(function() {
//                 html = '<img src="' + message.structured.payload.imageUrl + '" witdth="200" height="240" class="thumbnail" /><b>' +
//                   message.structured.payload.name + '<br>$' +
//                   message.structured.payload.price +
//                   '</b><br><a href="#" onclick="' + message.structured.payload.clickAction + '()">' +
//                   message.structured.payload.buttonLabel + '</a>';
//                 insertResponseMessage(html);
//               }, 1100);
//             } else {
//               console.log('not implemented');
//             }
//           }
//         } else {
//           insertResponseMessage('Oops, something went wrong. Please try again.');
//         }
//       }
//     })
//     .catch((error) => {
//       console.log('an error occurred', error);
//       insertResponseMessage('Oops, something went wrong. Please try again.');
//     });
// }

  $('.message-submit').click(function() {
    insertMessage();
  });

  $(window).on('keydown', function(e) {
    if (e.which == 13) {
      insertMessage();
      return false;
    }
  })

  function insertResponseMessage(content) {
    $('<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>').appendTo($('.mCSB_container'));
    updateScrollbar();

    setTimeout(function() {
      $('.message.loading').remove();
      $('<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' + content + '</div>').appendTo($('.mCSB_container')).addClass('new');
      setDate();
      updateScrollbar();
      i++;
    }, 500);
  }

});
