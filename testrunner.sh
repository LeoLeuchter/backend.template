#!/usr/bin/env sh

cd $(dirname $0)

MODULE_NAME=$(basename $(dirname $(find . ! -path "./build/*" ! -path "./venv/*" -name main.py)))

[ -z "${TMPDIR}" ] && TMPDIR=/tmp
TMP_DIR_PREFIX="${TMPDIR}/${MODULE_NAME}"
mkdir -p ${TMP_DIR_PREFIX}
[ -z "${TMP_DIR}" ] && TMP_DIR=$(mktemp -d "${TMPDIR}/${MODULE_NAME}/XXX")
[ -d "${TMP_DIR}" ] || exit 1

OK_TEXT="\e[32m OK \e[0m"
FAIL_TEXT="\e[31mFAIL\e[0m"
PYTEST_LOG="${TMP_DIR}/pytest.log"
PYRIGHT_LOG="${TMP_DIR}/pyright.log"
CODESPELL_LOG="${TMP_DIR}/codespell.log"
ERROR_LOG="${TMP_DIR}/error.log"
API_LOG="${TMP_DIR}/api.log"
API_PID_FILE="${TMP_DIR}/api.pid"
CONFIG_FILE="${TMP_DIR}"/config.json
API_URL="http://localhost:8000/docs/"
echo "{" >${CONFIG_FILE}
echo "  \"connection_string\":\"sqlite:///${TMP_DIR}/db.sqlite\"," >>${CONFIG_FILE}
echo "  \"log_level\":\"DEBUG\"" >>${CONFIG_FILE}
echo "}" >>${CONFIG_FILE}
reload="Y"

get_api_text() {
  if [ -e "${API_PID_FILE}" ]; then
    echo "API($(cat ${API_PID_FILE})): \e[32m${API_URL}\e[0m"
  else
    echo "API(): \e[31mNOT RUNNING\e[0m"
  fi
}

on_term() {
  reload="N"
  [ -f ${API_PID_FILE} ] && kill $(cat ${API_PID_FILE})
  # [ -f ${API_PID_FILE} ] && wait $(cat ${API_PID_FILE})
  [ -n "${animate_pid}" ] && kill -9 ${animate_pid} >/dev/null 2>&1
  [ -n "${kill_pid}" ] && kill -9 ${kill_pid} >/dev/null 2>&1
}

trap on_term TERM INT KILL

. ./venv/bin/activate

start_api() {
  if [ -f "${API_PID_FILE}" ]; then
    echo API ALREADY running
    sleep 4
  else
    CONFIG_FILE=${CONFIG_FILE} ./venv/bin/uvicorn ${MODULE_NAME}.main:app --reload --reload-dir ${MODULE_NAME} >${API_LOG} 2>&1 &
    ln -sf ${API_LOG} api.log
    pid=$!
    echo ${pid} >${API_PID_FILE}
    wait ${pid}
    rm ${API_PID_FILE}
  fi
}

start_api &

animate_sleep() {
  sleep 0.05 || sleep 1
}

animate() {
  while true; do
    printf '\r-'
    animate_sleep
    printf '\r/'
    animate_sleep
    printf '\r|'
    animate_sleep
    printf '\r\'
    animate_sleep
  done
}

run_pytest() {
  pytest --color=yes >${PYTEST_LOG} 2>&1
  return $?
}

run_pyright() {
  basedpyright --threads 4 $(ls -d */ | grep -v build | grep -v venv | grep -v .egg-info) >"${PYRIGHT_LOG}" 2>&1
  return $?
}

run_codespell() {
  codespell $(ls -d */ | grep -v build | grep -v venv | grep -v .egg-info) README.md >"${CODESPELL_LOG}" 2>&1
  return $?
}

clear
setterm -cursor off
animate &
animate_pid=$!

run_pytest &
pytest_pid=$!
run_pyright &
pyright_pid=$!
run_codespell &
codespell_pid=$!

# echo "" >${ERROR_LOG}
[ -e "${ERROR_LOG}" ] && rm ${ERROR_LOG}
pytest_ok="${OK_TEXT}"
wait ${pytest_pid} || {
  echo --- PYTEST --- >>${ERROR_LOG}
  tail -n 50 "${PYTEST_LOG}" >>${ERROR_LOG}
  pytest_ok="${FAIL_TEXT}"
}
pyright_ok="${OK_TEXT}"
wait ${pyright_pid} || {
  echo --- PYRIGHT --- >>${ERROR_LOG}
  tail -n 50 "${PYRIGHT_LOG}" >>${ERROR_LOG}
  pyright_ok="${FAIL_TEXT}"
}
codespell_ok="${OK_TEXT}"
wait ${codespell_pid} || {
  echo --- CODESPELL --- >>${ERROR_LOG}
  tail -n 50 "${CODESPELL_LOG}" >>${ERROR_LOG}
  codespell_ok="${FAIL_TEXT}"
}

kill ${animate_pid}
animate_pid=""

repaint() {
  clear
  [ -e "${API_LOG}" ] && {
    echo "--- API LOG ---"
    tail -n 50 ${API_LOG}
    echo
  }
  [ -e "${ERROR_LOG}" ] && {
    cat ${ERROR_LOG}
  }
  # \e[31mFAIL\e[0m"
  printf "API_NAME: \e[33m%s\e[0m pytest: %b pyright: %b spell: %b %b TMP_DIR: \e[33mfile://%s/\e[0m " "${MODULE_NAME}" "${pytest_ok}" "${pyright_ok}" "${codespell_ok}" "$(get_api_text)" "${TMP_DIR}"
}

monitor() {
  repaint
  exit_monitor="N"
  while [ "${reload}" = "Y" ] && [ "${exit_monitor}" = "N" ]; do
    inotifywait -t 1 --r . -e modify -e create -e delete -e move -e move_self >/dev/null 2>&1 &
    src_notify_pid=$!
    inotifywait -t 1 "${API_LOG}" -e modify -e create -e delete -e move -e move_self >/dev/null 2>&1 && repaint &
    api_notify_pid=$!
    wait ${src_notify_pid} && exit_monitor="Y"
    wait ${api_notify_pid} && repaint
  done
}

monitor &
kill_pid=$!
wait ${kill_pid}
sleep 1

if [ "${reload}" = "Y" ]; then
  echo RELOADING
  sleep 1
  TMP_DIR=${TMP_DIR} $0 $*
else
  echo TERMINATED
  rm -rf ${TMP_DIR}
fi
