// JavaScriptを使用して、client secretを取得する
const client_secret = document.getElementById('client_secret').value;
console.log('client_secret',client_secret)
// JavaScriptを使用して、Stripeのインスタンスを作成する
const stripe = Stripe('pk_test_51LedKvI8iZ48PSn6609eP61rSHlBUx2Vyna8tGZJ6CypIO5YWRCYgFD9XuxQtOJsJF170yZh92hCTE1Dp1b15JUh00Y61NzMPI', {locale: 'ja'});

// クレジットカード入力フォームで使用するElementsを設定し、上で取得したclient secretを渡す
var elements = stripe.elements();

// Custom styling can be passed to options when creating an Element.
var style = {
    base: {
      // Add your base input styles here. For example:
      fontSize: '16px',
      color: '#32325d',
    },
  };


// Payment Elementを作成し、既存のDOM要素から生成したDOM要素に置き換える
// var paymentElement = elements.create('payment');
// paymentElement.mount('#payment-element');
const card = elements.create('card',{
    hidePostalCode: true, 
    style: style});
card.mount('#card-element');


  card.on('change', function(event) {
    if (event.complete == true) {
      var formsubmit1 = document.getElementById('update');
      var formsubmit2 = document.getElementById('create');
        if(formsubmit1){
            formsubmit1.disabled = false;
        }else{
            formsubmit2.disabled = false;
        };
    }else{
      var formsubmit1 = document.getElementById('update');
      var formsubmit2 = document.getElementById('create');
        if(formsubmit1){
            formsubmit1.disabled = true;
        }else{
            formsubmit2.disabled = true;
        };
    }
  });

// id=payment-formの要素を取得する
var form = document.getElementById('payment-form');


$('#create').on('click', function (event) {

    event.preventDefault();

    stripe.createToken(card).then(function(result) {
        console.log("result", result)
        console.log("result.token", result.token)
        if (result.error) {
        // Inform the customer that there was an error.
        var errorElement = document.getElementById('card-errors');
        errorElement.textContent = result.error.message;
        } else {
        // Send the token to your server.

        $.ajax({
            type: "POST",
            url: "/card_create/",
            data: {
                'token_id': result.token.id,
            },
            dataType: 'json'

        }).done(function(data, textStatus, jqXHR) {
            console.log("aaaaaa",data)
                // 成功時のコールバック
                window.location.href = '/card/';

            }).fail(function(data, jqXHR, textStatus, errorThrown ) {
              // 失敗時のコールバック
            });

        }
    });
});

$('#update').on('click', function (event) {

    event.preventDefault();

    stripe.createToken(card).then(function(result) {
        if (result.error) {
        // Inform the customer that there was an error.
        var errorElement = document.getElementById('card-errors');
        errorElement.textContent = result.error.message;
        } else {
          // Send the token to your server.

          $.ajax({
              type: "POST",
              url: "/card_update/",
              data: {
                  'token_id': result.token.id,
              },
              dataType: 'json'

          }).done(function(data, textStatus, jqXHR) {
              console.log("aaaaaa",data)
                  // 成功時のコールバック
                  window.location.href = '/card/';

              }).fail(function(data, jqXHR, textStatus, errorThrown ) {
              // 失敗時のコールバック
              });

        };
    });
});
// クレジットカード情報が送信された時の処理を記述する
// form.addEventListener('submit', async (event) => {
//     event.preventDefault();

//     // confirmSetupを呼び出して支払い処理を完了させる
//     var {error} = await stripe.confirmSetup({
//         elements,
//         confirmParams: {
//             return_url: 'http://127.0.0.1:8000/card/',
//             }
//            });

//     if (error) {
//         var messageContainer = document.querySelector('#error-message');
//         messageContainer.textContent = error.message;
//     } else {
//         // none
//     }
// });
    // var update_form = document.getElementById('update-form');
    // update_form.addEventListener('submit', function(event) {
    // event.preventDefault();

        // var {error} = await stripe.createToken(paymentElement);

        // if (error) {
        //     stripeTokenHandler(result.token);
        // } else {
        //     // none
        // }

        // stripe.createToken(paymentElement).then(function(result) {
        //     stripeTokenHandler(result.token);
        //     if (result.error) {
        //     // Inform the user if there was an error.
        //     var errorElement = document.getElementById('card-errors');
        //     errorElement.textContent = result.error.message;
        //     } else {
        
        //     // Send the token to your server.
        //     stripeTokenHandler(result.token);
        //     }
    //     });
    // });

    // // Submit the form with the token ID.
    // function stripeTokenHandler(token) {
    // // Insert the token ID into the form so it gets submitted to the server
    // var update_form = document.getElementById('update-form');
    // var hiddenInput = document.createElement('input');
    // hiddenInput.setAttribute('type', 'hidden');
    // hiddenInput.setAttribute('name', 'stripeToken');
    // hiddenInput.setAttribute('value', token.id);
    // update_form.appendChild(hiddenInput);

    // Submit the form
    // update_form.submit();
    // }