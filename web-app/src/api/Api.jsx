import axios from 'axios'
import Cookies from 'js-cookie'

const getTokenRequest = (login, password) => {
  const requestURL = `api/token`
  const auth = {username: login, password: password}
  console.log(`Получение токена`, requestURL, `С авторизацией`, auth)
  return axios.get(requestURL, {auth: auth})
}

const getProfileRequest = (token) => {
  const requestURL = `api/user`
  const config = {headers: { Authorization: `Bearer ${token}` }}
  console.log(`Получение профиля`, requestURL, `с токеном`, token)
  return axios.get(requestURL, config)
}

const registrationRequest = (login, password, email) => {
  const requestURL = `api/registration`
  const body = {login: login, password: password, email: email}
  console.log(`Создание профиля`, requestURL)
  return axios.post(requestURL, body)
}

export const getToken = (component, login, password) => {
  component.setState({
    ...component.state,
    loading: {...component.state.loading, getToken: true},
    error: {errorCode: null, errorText: null}
  })
  getTokenRequest(login, password)
    .then(
      response => {
        const {data} = response
        Cookies.set('token', data.token)
        Cookies.set('user', {userRoles: data.data.user_roles, userLogin: login})
        console.log(`Получен ответ:`, data)
        component.setState({...component.state,
          loading: true,
          error: {errorCode: null, errorText: null},
          systems: data.data,
          needReload: false
        })
      }
    )
  .catch((error) => {
    console.log(`Результат запроса:`, error)
    let errorText
    if (error.response.status === 401) {
      errorText = "Неверное имя учётной записи или пароль!"
    } else if (error.response.status === 500) {
      errorText = "Ошибка сервера!"
    }
    Cookies.remove('token')
    Cookies.remove('user')
    component.setState({...component.state,
      loading: false,
      error: {errorCode: error.status, errorText: errorText}
    })
  });
}


export const getProfile = (component, token) => {
  component.setState({
    ...component.state,
    loading: {...component.state.loading, getProfile: true},
    error: {errorCode: null, errorText: null}
  })
  getProfileRequest(token)
    .then(
      response => {
        const {data} = response
        Cookies.set('token', data.token)
        Cookies.set('user', {userRoles: data.data.user_roles, userLogin: data.data.login})
        console.log(`Получен ответ:`, data)
        component.setState({...component.state,
          loading: {...component.state.loading, getProfile: false},
          error: {errorCode: null, errorText: null},
          profile: data.data,
          needReload: false
        })
      }
    )
  .catch((error) => {
    console.log(`Результат запроса:`, error)
    let errorText
    if (error.response.status === 401) {
      errorText = "Неверное имя учётной записи или пароль!"
    } else if (error.response.status === 500) {
      errorText = "Ошибка сервера!"
    }
    Cookies.remove('token')
    Cookies.remove('user')
    component.setState({...component.state,
      loading: {...component.state.loading, getToken: false},
      error: {errorCode: error.response.status, errorText: errorText}
    })
  });
}

export const registration = (component, login, password, email) => {
  component.setState({
    ...component.state,
    loading: true,
    error: {errorText: null}
  })
  registrationRequest(login, password, email)
    .then(
      response => {
        const {data} = response
        console.log(`Получен ответ:`, data)
        component.setState({...component.state,
          loading: false,
          error: {errorText: null},
          success: true
        })
      }
    )
  .catch((error) => {
    console.log(`Результат запроса:`, error)
    let errorText
    if (error.response.status === 400) {
      errorText = "Не заполнены обязательные поля"
    } else if (error.response.status === 500) {
      errorText = "Ошибка сервера!"
    }
    component.setState({...component.state,
      loading: false,
      error: {errorText: errorText}
    })
  });
}

export default getToken