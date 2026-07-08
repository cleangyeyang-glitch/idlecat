# IdleCat — 유휴 감지 픽셀 고양이

presented by g.ad.c 2026

일정 시간 입력이 없으면 픽셀 고양이가 화면 하단을 산책하는 데스크톱 펫.
걷기 · 달리기 · 앉기 · 그루밍 · 기지개 · 잠자기 · 클릭 시 점프 후 도망.

## 실행파일 받는 법 (GitHub Actions 자동 빌드)

1. GitHub에서 새 저장소(repository) 생성 — Private 무방
2. 이 폴더의 파일 전체를 저장소에 업로드 (`.github/workflows/build.yml` 경로 유지 필수)
3. 업로드(push)하면 자동으로 빌드가 시작됨
4. 저장소의 **Actions 탭** → 최신 워크플로 실행 클릭 → 하단 **Artifacts**에서 다운로드
   - `IdleCat-Windows` : IdleCat.exe
   - `IdleCat-macOS-AppleSilicon` : M1/M2/M3/M4 Mac용 IdleCat.app
   - `IdleCat-macOS-Intel` : Intel Mac용 IdleCat.app

빌드는 3~5분 정도 걸립니다. 이후 파일을 수정해 push할 때마다 자동으로 다시 빌드됩니다.

## 참고

- macOS: 서명되지 않은 앱이므로 첫 실행 시 우클릭 → 열기 필요
- Windows: SmartScreen 경고가 뜨면 "추가 정보 → 실행" 선택
- 유휴 시간 변경: 실행 시 인자로 초 단위 지정 (예: `IdleCat.exe 30`)

## 직접 빌드 (선택)

각 OS에서 Python 설치 후:

    pip install pyinstaller
    # Windows
    pyinstaller --onefile --noconsole --name IdleCat idle_cat.py
    # macOS
    pyinstaller --onefile --windowed --name IdleCat idle_cat.py
