$(function(){

    // jquery validateを使ったフロントエンドバリデーション
    $.extend($.validator.messages, {
        email: '正しいメールアドレスを入力して下さい。',
        equalTo: 'もう一度同じ値を入力して下さい。',
        minlength: '{0}文字以上入力して下さい。',
        required: '入力して下さい。',
        digits: '整数を入力してください',
    });

    $('form').validate({
        rules: {
            'user-email': {
                required: true,
                // email: true,
                // CustomValidateEmail: true,
            },
            "company-pic_company_name": {
                // CustomValidateUserCompanyName: true,
                required: true,
                // CustomValidateUserCompanyName: {
                //       depends: function(element) {
                //         // 個人事業主にチェックが入っている場合は法人格のチェックをしない
                //         return !($('input:checked').val() == 'on');
                //       }
                // },
            },
        },
        messages: {
            "user-email": {
                required: 'メールアドレスは必須です。',
                // email: '正しいメールアドレスを入力してください。',
                // CustomValidateEmail: 'このメールアドレスは使用できません。',
            },
            "company-pic_company_name": {
                required: '会社名は必須です。',
                CustomValidateUserCompanyName: '法人格を入力してください',
            },
        },
        errorPlacement: function(error, element) {
          // console.log(error)
          // console.log(element)
          // error.insertAfter($("#" + element.attr("name") + "_err") )
          error.insertAfter($("#" + element.attr("name")))
        },
    });
    // メールアドレス用カスタムバリデーション
    // jQuery.validator.addMethod(
    //   "CustomValidateEmail",
    //   function(val,elem){
    //     // console.log(val);
    //     // console.log(elem);
    //     reg = new RegExp(/([\w]+@[\w]+?\.?(ocn\.ne\.jp|so-net\.ne\.jp|biglobe\.ne\.jp|nifty\.com|asahi-net\.or\.jp|wakwak\.com|plala\.or\.jp|yahoo\.co\.jp|hotmail\.com|hotmail\.co\.jp|ybb\.ne\.jp))|([\w]+@(ocn\.ne\.jp|so-net\.ne\.jp|biglobe\.ne\.jp|nifty\.com|asahi-net\.or\.jp|wakwak\.com|plala\.or\.jp|yahoo\.co\.jp|hotmail\.com|hotmail\.co\.jp|ybb\.ne\.jp))/);
    //     // console.log(reg);
    //     // console.log('テスト　バル')
    //     // console.log(reg.test(val));
    //     // console.log('オプション　エルム')
    //     // console.log(this.optional(elem));
    //     // console.log('メール　かつ')
    //     // console.log(this.optional(elem) || !reg.test(val));
    //     // console.log('メール　＆＆')
    //     // console.log(this.optional(elem) && reg.test(val));
    //     return this.optional(elem) || !reg.test(val);
    //   },
    //   ""
    // );

    // 会社名用カスタムバリデーション
    jQuery.validator.addMethod(
      "CustomValidateUserCompanyName",
      function(val,elem){
        // console.log(val);
        // console.log(elem);
        reg = new RegExp("(^(株式会社|合同会社|合名会社|合資会社|一般社団法人|一般財団法人|特定非営利活動法人|有限責任事業組合).*)|(^.*(株式会社|合同会社|合名会社|合資会社|一般社団法人|一般財団法人|特定非営利活動法人|有限責任事業組合))");
        // console.log(reg);
        // console.log(reg.test(val));
        // console.log(this.optional(elem));
        // console.log(this.optional(elem) || reg.test(val));
        return this.optional(elem) || reg.test(val);
      },
      ""
    );

    // パスワードの強化チェック用バリデーション
    var $form = $(".password_form");

    // submitイベントをキャンセル
    function formCancelSubmit(){
      $form.off("submit").on("submit", function(e){
        alert("パスワードの強度が基準値に達していません。\n数字や記号を追加し文字数を増やしてください。");
        e.preventDefault();
      });
    }

    $("#user-password1").pwdMeasure({
      minScore: 50,
      minlength: 8,
      indicator: "#pm-indicator",
      confirm: "#user-password2",
      indicatorTemplate: "パスワード判定: <%= label %>",
      events: "keyup",
      labels: [
        {score:45, label:"NG", className:"weak"},
        {score:100, label:"OK", className:"strong"},
        {score:"notMatch", label:"不一致", className:"not-match"},
        {score:"empty", label:"未入力", className:"empty"}
      ],
      onValid: function(percentage, label, className){
        $form.off("submit");
        $('#send').prop("disabled", false)
        $form.off("submit");
      },
      onInvalid: function(percentage, label, className){
        formCancelSubmit();
      },
      onNotMatch: function(label,className){
        $('#send').prop("disabled", true)
      },
    });

    // フロントエンドでemailの重複チェック
    // $("#user-email").change(function () {
    //   var email = $(this).val();
    //   var email_name = $(this).attr("name");
    //   console.log("重複チェック");
    //   console.log(email_name);
    //   $.ajax({
    //     url: 'validate_email/',
    //     data: {
    //       'email': email
    //     },
    //     dataType: 'json',
    //     success: function (data) {
    //       if (data.is_exist) {
    //         $("#user-email_err").text(data.error_message);
    //       }
    //     }
    //   });
    //
    // });

});
