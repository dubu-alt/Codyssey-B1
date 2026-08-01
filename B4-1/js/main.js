// var 사용 금지: 이 파일 전체에서 const/let만 사용
// "사용자 이벤트 → 상태 변경 → 화면 업데이트" 패턴을 위한 중앙 상태 객체
// 상태(state)를 한 곳에 모아두면, 어떤 이벤트가 어떤 값을 바꾸는지 추적하기 쉬워짐
const state = {
  projects: [],           // GitHub API로 받아온 전체 프로젝트 목록
  filteredProjects: [],    // 필터가 적용된 뒤 실제로 화면에 보여줄 목록
  currentFilter: 'all',    // 현재 선택된 언어 필터 (보너스: 프로젝트 필터링)
  isMenuOpen: false,       // 모바일 햄버거 메뉴 열림/닫힘 상태
};

// DOM 요소를 미리 한 번에 찾아서 selectors 객체에 모아둠
// -> 매번 querySelector를 반복 호출하지 않아도 되고, 요소 이름을 한눈에 파악 가능
// data-* 속성을 셀렉터로 사용하는 이유: class는 스타일 전용, data-*는 JS 동작 전용으로 역할을 분리하기 위함
const selectors = {
  header: document.querySelector('[data-header]'),
  menu: document.querySelector('[data-menu]'),
  menuToggle: document.querySelector('[data-menu-toggle]'),
  themeToggle: document.querySelector('[data-theme-toggle]'),
  topButton: document.querySelector('[data-top-button]'),
  projectSection: document.querySelector('[data-github-username]'),
  projectList: document.querySelector('[data-project-list]'),
  projectStatus: document.querySelector('[data-project-status]'),
  filterGroup: document.querySelector('[data-filter-group]'),
  retryProjects: document.querySelector('[data-retry-projects]'),
  contactForm: document.querySelector('[data-contact-form]'),
  formSuccess: document.querySelector('[data-form-success]'),
  formError: document.querySelector('[data-form-error]'),
  submitButton: document.querySelector('[data-contact-form] button[type="submit"]'),
  currentYear: document.querySelector('[data-current-year]'),
  typing: document.querySelector('[data-typing]'),
};

// 모바일 햄버거 메뉴 토글 구현
// 이벤트(버튼 클릭) → 상태 변경(state.isMenuOpen) → 화면 업데이트(classList, aria 속성) 흐름의 대표 예시 ①
const setMenuState = (isOpen) => {
  state.isMenuOpen = isOpen;
  selectors.menu.classList.toggle('is-open', isOpen); // CSS에서 .is-open일 때 메뉴가 보이도록 처리
  selectors.menuToggle.setAttribute('aria-expanded', String(isOpen)); // 접근성: 메뉴 확장 여부 알림
  selectors.menuToggle.setAttribute('aria-label', isOpen ? '메뉴 닫기' : '메뉴 열기');
};

// 스크롤 60px 이상 → 네비게이션 배경색 변경 / 스크롤 300px 이상 → 탑 버튼 표시
// 이벤트(scroll) → 상태 확인(scrollY) → 화면 업데이트(classList.toggle) 흐름의 대표 예시 ②
const updateScrollUi = () => {
  const scrollY = window.scrollY;
  selectors.header.classList.toggle('is-scrolled', scrollY >= 60);   // 커스텀 설정값: 60px
  selectors.topButton.classList.toggle('is-visible', scrollY >= 300); // 커스텀 설정값: 300px
};

// [보너스] 다크 모드 초기값 결정 로직
// 1순위: localStorage에 저장된 사용자의 마지막 선택
// 2순위(보너스): prefers-color-scheme으로 OS/브라우저의 시스템 테마 감지
const getInitialTheme = () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    return savedTheme;
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

// 실제로 <html data-theme="..."> 속성을 바꿔서 base.css의 [data-theme="dark"] 변수들이 적용되게 함
const applyTheme = (theme) => {
  document.documentElement.dataset.theme = theme;
  selectors.themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
  selectors.themeToggle.setAttribute('aria-label', theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환');
};

// 다크 모드 전환 및 로컬스토리지 유지
// 이벤트(테마 버튼 클릭) → 상태 변경(localStorage 저장) → 화면 업데이트(applyTheme) 흐름의 대표 예시 ③
const toggleTheme = () => {
  const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', nextTheme); // 새로고침해도 선택한 테마가 유지되도록 저장
  applyTheme(nextTheme);
};

// Intersection Observer를 이용한 스크롤 애니메이션 (임계값 0.2 이상)
// .reveal 클래스가 붙은 요소가 뷰포트에 20% 이상 보이면 .is-visible을 추가해 CSS 트랜지션 실행
const setupRevealAnimation = () => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target); // 한 번 나타난 뒤에는 더 이상 관찰할 필요 없으므로 해제 (성능 최적화)
      }
    });
  }, { threshold: 0.2 }); // 커스텀 설정값: 0.2 (요소의 20%가 보이면 콜백 실행)

  document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
};

// [보너스] Hero 섹션 타이핑 애니메이션
// 여러 문구를 한 글자씩 타이핑하고, 다 쓰면 한 글자씩 지운 뒤 다음 문구로 넘어가는 재귀적 setTimeout 패턴
const typeHeroText = () => {
  const phrases = ['프론트엔드 개발자', '문제를 해결하는 사람', '꾸준히 성장하는 동료'];
  let phraseIndex = 0; // 현재 문구의 인덱스
  let charIndex = 0;   // 현재까지 타이핑된 글자 수
  let isDeleting = false; // 글자를 지우는 중인지 여부

  const tick = () => {
    const currentPhrase = phrases[phraseIndex];
    selectors.typing.textContent = currentPhrase.slice(0, charIndex);

    // 타이핑 중이고 아직 문구를 다 쓰지 않았다면 한 글자 더 추가
    if (!isDeleting && charIndex < currentPhrase.length) {
      charIndex += 1;
      setTimeout(tick, 110);
      return;
    }

    // 문구를 다 썼다면 잠시 멈췄다가 삭제 모드로 전환
    if (!isDeleting && charIndex === currentPhrase.length) {
      isDeleting = true;
      setTimeout(tick, 1300);
      return;
    }

    // 삭제 중이고 아직 글자가 남아있다면 한 글자 지움
    if (isDeleting && charIndex > 0) {
      charIndex -= 1;
      setTimeout(tick, 55);
      return;
    }

    // 다 지웠다면 다음 문구로 순환 이동
    isDeleting = false;
    phraseIndex = (phraseIndex + 1) % phrases.length;
    setTimeout(tick, 250);
  };

  tick();
};

// 프로젝트 로딩/에러/빈 상태 메시지를 화면에 표시하는 공통 함수
const renderStatus = (message) => {
  selectors.projectStatus.textContent = message;
};

// ES6+ 문법 적용: 구조분해 할당(destructuring)으로 GitHub API 응답 객체에서 필요한 값만 추출
// createElement로 DOM을 직접 만들어 innerHTML을 쓰지 않음 (XSS 방지 + 명확한 구조)
const createProjectCard = ({ name, description, html_url: htmlUrl, language, stargazers_count: stars, forks_count: forks }) => {
  const card = document.createElement('article');
  const title = document.createElement('h3');
  const link = document.createElement('a');
  const summary = document.createElement('p');
  const meta = document.createElement('div');
  const metaItems = [language || '기타', `★ ${stars}`, `⑂ ${forks}`]; // 템플릿 리터럴 사용

  card.className = 'project-card';
  link.href = htmlUrl;
  link.target = '_blank';
  link.rel = 'noopener noreferrer'; // 새 탭에서 열 때 보안을 위한 속성 (window.opener 접근 차단)
  link.textContent = name;
  title.append(link);
  summary.textContent = description || '설명이 준비 중인 프로젝트입니다.';
  meta.className = 'project-card__meta';
  // 배열 메서드(map) 활용: 메타 정보 배열을 span 요소 배열로 변환
  meta.append(...metaItems.map((item) => {
    const span = document.createElement('span');
    span.textContent = item;
    return span;
  }));
  card.append(title, summary, meta);
  return card;
};

// 성공/빈 상태 UI 분기 렌더링
const renderProjects = () => {
  selectors.projectList.replaceChildren(); // 기존 카드 목록을 비움 (재렌더링 전 초기화)

  if (state.filteredProjects.length === 0) {
    renderStatus('표시할 프로젝트가 없습니다'); // 빈 상태 메시지
    return;
  }

  const cards = state.filteredProjects.map(createProjectCard);
  selectors.projectList.append(...cards);
  renderStatus(`${state.filteredProjects.length}개의 프로젝트를 표시하고 있습니다.`);
};

// [보너스] 프로젝트 필터링: array.filter()로 선택된 언어에 해당하는 프로젝트만 추출
// 이벤트(필터 버튼 클릭) → 상태 변경(state.currentFilter) → 화면 업데이트(renderProjects) 흐름의 대표 예시 ④
const applyProjectFilter = (filter) => {
  state.currentFilter = filter;
  state.filteredProjects = filter === 'all'
    ? state.projects
    : state.projects.filter(({ language }) => (language || '기타') === filter);

  // 현재 선택된 필터 버튼에만 is-active 클래스를 부여해 시각적으로 표시
  selectors.filterGroup.querySelectorAll('.filter-button').forEach((button) => {
    button.classList.toggle('is-active', button.dataset.filter === filter);
  });
  renderProjects();
};

// [보너스] 프로젝트 목록에서 사용된 언어 종류를 추출해 필터 버튼을 동적으로 생성
// Set을 이용해 중복 언어를 제거(고유값만 남김)
const renderFilters = () => {
  const languages = [...new Set(state.projects.map(({ language }) => language || '기타'))].sort();
  const buttons = languages.map((language) => {
    const button = document.createElement('button');
    button.className = 'filter-button';
    button.type = 'button';
    button.dataset.filter = language;
    button.textContent = language;
    return button;
  });

  // "전체" 버튼을 제외한 기존 언어 필터 버튼들을 제거한 뒤 새로 생성한 버튼으로 교체
  selectors.filterGroup.querySelectorAll('[data-filter]:not([data-filter="all"])').forEach((button) => button.remove());
  selectors.filterGroup.append(...buttons);
};

// fetch + async/await로 GitHub API 호출, try/catch로 비동기 에러 처리
const fetchProjects = async () => {
  const username = selectors.projectSection.dataset.githubUsername;
  renderStatus('로딩 중...'); // 로딩 상태 UI
  selectors.projectList.replaceChildren();

  try {
    const response = await fetch(`https://api.github.com/users/${username}/repos?sort=updated&per_page=12`);

    // GitHub API 레이트 리밋(403) 에러를 구분해서 사용자에게 명확히 안내
    if (response.status === 403) {
      throw new Error('GitHub API 요청 제한에 도달했습니다. 잠시 후 다시 시도해 주세요.');
    }

    if (!response.ok) {
      throw new Error('프로젝트를 불러올 수 없습니다'); // 일반 에러 상태 메시지
    }

    const repos = await response.json();
    // ES6+ 배열 메서드(filter, map)와 구조분해 할당을 조합해 필요한 데이터만 정제
    state.projects = repos
      .filter(({ fork }) => !fork) // 포크한 저장소는 제외하고 본인이 만든 프로젝트만 표시
      .map(({ id, name, description, html_url, language, stargazers_count, forks_count }) => ({
        id,
        name,
        description,
        html_url,
        language,
        stargazers_count,
        forks_count,
      }));
    renderFilters();
    applyProjectFilter('all');
  } catch (error) {
    // 에러 상태: 에러 메시지 표시 + 재시도 버튼으로 재요청 유도
    state.projects = [];
    state.filteredProjects = [];
    selectors.projectList.replaceChildren();
    renderStatus(`${error.message} — 재시도 버튼을 눌러 다시 불러와 주세요.`);
  }
};

// 입력 필드 근처에 에러 메시지를 표시하고, aria 속성으로 접근성을 함께 챙김
const setFieldError = (field, message) => {
  const errorElement = document.querySelector(`#${field.id}-error`); // 템플릿 리터럴로 에러 요소 id 조합
  field.setAttribute('aria-invalid', message ? 'true' : 'false'); // 스크린리더에 입력 오류 여부 전달
  field.setAttribute('aria-describedby', errorElement.id); // 어떤 요소가 에러 설명인지 연결
  errorElement.textContent = message;
};

// 필수값(이름/이메일/메시지) 검사 + 이메일 형식 검사
const validateContactForm = () => {
  const formData = new FormData(selectors.contactForm);
  const values = Object.fromEntries(formData.entries()); // FormData를 일반 객체로 변환 (ES6+)
  const fields = {
    name: selectors.contactForm.elements.name,
    email: selectors.contactForm.elements.email,
    message: selectors.contactForm.elements.message,
  };
  const errors = {
    name: values.name.trim() ? '' : '이름을 입력해 주세요.',
    // 정규식으로 간단한 이메일 형식(문자@문자.문자)인지 검사
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim()) ? '' : '올바른 이메일 형식으로 입력해 주세요.',
    message: values.message.trim() ? '' : '메시지를 입력해 주세요.',
  };

  Object.entries(fields).forEach(([key, field]) => setFieldError(field, errors[key]));
  return Object.values(errors).every((message) => message === ''); // 모든 에러 메시지가 빈 문자열이면 통과
};

const setSubmitting = (isSubmitting) => {
  selectors.submitButton.disabled = isSubmitting;
  selectors.submitButton.textContent = isSubmitting ? '전송 중...' : '메시지 보내기';
};

const sendToFormspree = async (formData) => {
  const endpoint = selectors.contactForm.dataset.formspreeEndpoint;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { Accept: 'application/json' },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('전송에 실패했습니다. 잠시 후 다시 시도해 주세요.');
  }
};

// event.preventDefault()로 기본 폼 제출(새로고침)을 막고 JS로 직접 제어
// 이벤트(폼 제출) → 상태 변경(유효성 검사 결과) → 화면 업데이트(에러/성공 메시지) 흐름의 대표 예시 ⑤
const handleFormSubmit = async (event) => {
  event.preventDefault();
  selectors.formSuccess.textContent = '';
  selectors.formError.textContent = '';

  if (!validateContactForm()) {
    return;
  }

  const formData = new FormData(selectors.contactForm);
  setSubmitting(true);

  try {
    await sendToFormspree(formData);
    selectors.contactForm.reset();
    selectors.formError.textContent = ''; // 폼 제출 성공 시 에러 메시지 초기화
    selectors.formSuccess.textContent = '메시지가 성공적으로 전송되었습니다. 빠르게 확인하겠습니다!';
  } catch (error) {
    selectors.formSuccess.textContent = '';
    selectors.formError.textContent = error.message;
  } finally {
    setSubmitting(false);
  }
};

// 인라인 onclick 대신 addEventListener로 이벤트를 등록
const bindEvents = () => {
  selectors.menuToggle.addEventListener('click', () => setMenuState(!state.isMenuOpen));
  selectors.themeToggle.addEventListener('click', toggleTheme);
  // 스크롤 탑 버튼 클릭 시 부드럽게 최상단으로 이동
  selectors.topButton.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  selectors.retryProjects.addEventListener('click', fetchProjects);
  selectors.contactForm.addEventListener('submit', handleFormSubmit);
  // passive: true → 스크롤 성능 최적화 (이 리스너가 스크롤을 막지 않는다고 브라우저에 미리 알림)
  window.addEventListener('scroll', updateScrollUi, { passive: true });

  // 이벤트 위임(event delegation): 메뉴 안의 링크 하나하나에 리스너를 달지 않고 부모(ul)에서 한 번에 처리
  selectors.menu.addEventListener('click', (event) => {
    if (event.target.matches('a')) {
      setMenuState(false); // 모바일에서 메뉴 링크 클릭 시 메뉴를 자동으로 닫음
    }
  });

  // [보너스] 필터 버튼도 이벤트 위임으로 처리 (동적으로 추가된 버튼도 자동으로 동작함)
  selectors.filterGroup.addEventListener('click', (event) => {
    const button = event.target.closest('[data-filter]');
    if (button) {
      applyProjectFilter(button.dataset.filter);
    }
  });
};

// 페이지 로드 시 실행되는 초기화 함수: 화면에 필요한 모든 기능을 순서대로 준비
const init = () => {
  selectors.currentYear.textContent = new Date().getFullYear(); // Footer의 저작권 연도를 자동으로 채움
  applyTheme(getInitialTheme());
  bindEvents();
  updateScrollUi();       // 새로고침 시 이미 스크롤된 상태를 반영하기 위해 최초 1회 실행
  setupRevealAnimation();
  typeHeroText();
  fetchProjects();
};

// script가 defer로 로드되므로 DOM이 이미 준비된 상태 -> DOMContentLoaded 없이 바로 실행 가능
init();
