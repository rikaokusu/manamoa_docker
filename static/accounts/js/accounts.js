// colorbox用
// 別HTMLをモーダルで表示
$(".iframe").colorbox({iframe:true, width:"80%", height:"80%"});


$(function(){

  // 閉じるボタンをスクロール時は非表示
  $(window).on("scroll touchmove", function(){ //スクロール中に判断する
      $(".bar_button").stop(); //アニメーションしている場合、アニメーションを強制停止
      $(".bar_button").css('display', 'none').delay(500).fadeIn('fast');
      //スクロール中は非表示にして、500ミリ秒遅らせて再び表示
  });

});
