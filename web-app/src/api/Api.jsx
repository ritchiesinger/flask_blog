import axios from 'axios'
import Cookies from 'js-cookie'

const backEndpoint = "http://localhost:5000/api"

const getTokenRequest = (login, password) => {
  const requestURL = `${backEndpoint}/token`
  const auth = {username: login, password: password}
  console.log(`Получение токена`, requestURL, `С авторизацией`, auth)
  return axios.get(requestURL, {auth: auth});
}

const getProfileRequest = (token) => {
  const requestURL = `${backEndpoint}/user`
  const config = {headers: { Authorization: `Bearer ${token}` }}
  console.log(`Получение профиля`, requestURL, `с токеном`, token)
  return axios.get(requestURL, config);
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
          loading: {...component.state.loading, getToken: false},
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
      loading: {...component.state.loading, getToken: false},
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

export default getToken