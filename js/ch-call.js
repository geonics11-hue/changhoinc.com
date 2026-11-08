/*! Phone call click detection (MIT)
 *  Detects: click on a tel: link. Pushes dataLayer event: phone_click
 *  From the conversion-tracking skill in Marketing Skills
 *
 *  창호종합기계 적용 (2026-11-08): 이 사이트는 구글 태그 관리자(GTM) 없이 gtag 만 쓴다.
 *  그래서 원본의 dataLayer.push({event:...}) 한 줄만 gtag('event','phone_click',...) 로 바꿨다.
 *  나머지 줄은 원본 그대로다(page_path 1줄만 뺐다 · 아래 설명). 싣는 값 = 누른 회사 번호(사이트에 공개된 번호)·링크 글자.
 *  손님 정보·금액은 싣지 않는다. 카톡 채널 링크(pf.kakao.com)도 이 파일이 kakao_click 으로 센다. */
(function () {
  if (window.__ctDetectPhoneClick) return;
  window.__ctDetectPhoneClick = true;
  window.dataLayer = window.dataLayer || [];

  // A click is a call INTENT, not a completed call. On desktop especially,
  // many tel: clicks never become a conversation. Count it as a lead signal,
  // and prefer a call tracking number if you need answered-call accuracy.

  // Ignore a repeat click on the same number inside this window. Impatient
  // double-taps on mobile are common and would otherwise double count.
  var DEDUPE_MS = 2000;
  var lastNumber = null;
  var lastAt = 0;

  function normalise(href) {
    // tel:+61 (2) 1234-5678 -> +61212345678 . Keeps a leading +, drops the
    // punctuation humans put in phone numbers so dedupe compares like for like.
    var raw = String(href || '').replace(/^tel:/i, '');
    try { raw = decodeURIComponent(raw); } catch (e) { /* leave as-is */ }
    var plus = raw.trim().charAt(0) === '+' ? '+' : '';
    return plus + raw.replace(/[^0-9]/g, '');
  }

  function handleClick(event) {
    try {
      // Left click only, and not a modified click that opens elsewhere.
      if (event.button !== undefined && event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      var target = event.target;
      if (!target || !target.closest) return;

      // closest() because the click usually lands on an icon or span INSIDE
      // the anchor, not the anchor itself.
      // 창호종합기계(2026-11-08 나나파파 「전화 파일에 카톡 추가」): 카카오 채널 링크는 kakao_click 으로 센다.
      // 구글 애널리틱스 「이벤트 만들기」 화면이 click 을 기준으로 고를 수 없어 코드로 보낸다.
      var kakao = target.closest('a[href*="pf.kakao.com"]');
      if (kakao) {
        var kNow = new Date().getTime();
        if (lastNumber === 'kakao' && (kNow - lastAt) < DEDUPE_MS) return;
        lastNumber = 'kakao';
        lastAt = kNow;
        if (typeof window.gtag !== 'function') return;
        window.gtag('event', 'kakao_click', {
          link_text: (kakao.textContent || '').trim().slice(0, 100)
        });
        return;
      }

      var link = target.closest('a[href^="tel:"], a[href^="TEL:"]');
      if (!link) return;

      var number = normalise(link.getAttribute('href'));
      if (!number) return;

      var now = new Date().getTime();
      if (number === lastNumber && (now - lastAt) < DEDUPE_MS) return;
      lastNumber = number;
      lastAt = now;

      // 창호종합기계: 원본의 window.dataLayer.push({event:'phone_click',...}) 대신 gtag 로 보낸다.
      if (typeof window.gtag !== 'function') return;
      window.gtag('event', 'phone_click', {
        phone_number: number,
        // The visible text, useful when a site shows different numbers per
        // location or campaign. Trimmed and capped so a whole button's worth
        // of markup text never lands in the dataLayer.
        link_text: (link.textContent || '').trim().slice(0, 100)
        // 창호종합기계: 원본의 page_path 는 뺐다 — gtag 에서는 쪽 주소 칸(dp)을 덮어쓰는 예약 이름이고,
        // 쪽 주소는 구글 태그가 이미 함께 보낸다(2026-11-08 시험에서 dp 로 바뀌는 것 확인).
      });
    } catch (e) {
      // Never throw back into the page's own click handling.
    }
  }

  // Bubble phase: a tel: click has no validation to lose a race with, and
  // bubbling means anything that legitimately cancels the click wins first.
  document.addEventListener('click', handleClick, false);
})();
