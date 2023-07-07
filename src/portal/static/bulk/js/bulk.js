$(function() {

    // Get the template HTML and remove it from the doumenthe template HTML and remove it from the document
    var previewNode = document.querySelector("#template");
    // #templateというIDがあるときのみ処理
    if (previewNode) {
      console.log(previewNode);
      previewNode.id = "";
      var previewTemplate = previewNode.parentNode.innerHTML;
      previewNode.parentNode.removeChild(previewNode);
    }

    Dropzone.options.myAwesomeDropzone = { // The camelized version of the ID of the form element
       // The configuration we've talked about above
       autoProcessQueue: false,
       maxFiles: 1,
       maxFilesize: 0.5, // MiB
       acceptedFiles: ".csv, text/csv",
       paramName: "file",
       dictDefaultMessage: "アップロードしたいファイルをここにドラッグ&ドロップしてください<br /> <div class='basebluebtn'>またはファイルを選択</div>",
       previewTemplate: previewTemplate,
       previewsContainer: "#previews",

       // The setting up of the dropzone
       init: function() {
           var myDropzone = this;

           // ドラッグ&ドロップ領域以外にファイルをドラッグ&ドロップしても反応しないようにする
           $(document).on('drop dragover', function (e) {
             e.stopPropagation();
             e.preventDefault();
           });

           // ファイルを追加したときにボタンを有効化する
           myDropzone.on("addedfile", function(file) {
             $("#bar_button").stop().animate({bottom:'0'},1200);
           });

           // ファイルを削除したときにボタンを無効化する
           myDropzone.on("removedfile", function(file) {
             $("#bar_button").stop().animate({bottom:'-80px'},1200);

           });

           $("#submit_all").click(function (e) {
               e.preventDefault();
               myDropzone.processQueue();

           });

           // Update the total progress bar
            myDropzone.on("totaluploadprogress", function(progress) {
              $(".progress-bar").css("width" , progress + "%");
              $(".progress-text").text = progress + "%";
            });


       },
       maxfilesexceeded:  function(file) {
          // thisオブジェクトが変わるため、変数に格納しておく
          var myDropzone = this;
          // モーダルを表示する
          $('#removeModal').modal('show')
          // 置き換えるボタンがクリックされた場合
          $("#removeModalButton").click(function (e) {
            // モーダルを非表示
            $('#removeModal').modal('hide')
            // 旧ファイルを削除して新しいファイルを追加する(置き換える)
            myDropzone.removeAllFiles();
            myDropzone.addFile(file);
          });
       },
       // アップロードが成功またはエラーが発生したときファイルを削除する。
       complete: function(file, respnese){
         this.removeFile(file);
       },
       // アップロード成功時にメッセージを表示する。
       success: function(file, response){
           $('#validation-error').html('<div class="alert alert-success" role="alert">' + response["messages"] + '</div>');
       },
       // アップロード失敗時にメッセージを表示する。
       error: function(file, response, xhr){
           // フロントエンドでエラーが発生した場合。(サーバからのレスポンスがないエラー)
           if (xhr == null) {
               // 2つ以上のファイルアップロードの場合
               if (response == "You can not upload any more files.") {
                 // エラーを表示しない
               } else if (response == "You can't upload files of this type.") {
                
                 $('#validation-error').html('<div class="alert alert-danger" role="alert">' + gettext("UPLOAD CSV FILE") + '</div>');
               } else if (!response.indexOf("File is too big")) {
                 $('#validation-error').html('<div class="alert alert-danger" role="alert">' + "ファイルサイズ上限(0.5MB)を超えています。サイズを小さくしてください。" + '</div>');
               } else {
                 $('#validation-error').html('<div class="alert alert-danger" role="alert">' + response + '</div>');
               }
          　// サーバーからレスポンスが帰ってきた場合(サーバ側でエラーが発生した場合)
           } else {
             $('#validation-error').html('<div class="alert alert-danger" role="alert">' + response["messages"] + '</div>');
           }
       },
    };

});