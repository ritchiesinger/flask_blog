import React, {Component} from 'react'
import { Navigate } from "react-router-dom"
import getToken from '../api/Api'
import Cookies from 'js-cookie'
import logo from '../assets/reactLogo.png'


export default class LoginPage extends Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: {},
      error: {errorCode: null, errorText: null},
      success: null,
      loginForm: {inputLogin: "", inputPassword: ""}
    }
  }
  componentDidUpdate = () => {}
  handleSearchFormChange = (event) => {
    switch (event.currentTarget.id) {
    case 'inputLogin':
      this.setState({...this.state,
        loginForm: {...this.state.loginForm, inputLogin: event.currentTarget.value}})
      break
    case 'inputPassword':
      this.setState({...this.state,
        loginForm: {...this.state.loginForm, inputPassword: event.currentTarget.value}})
      break
    default:
      break
    }
  }
  login = () => {
    getToken(this, this.state.loginForm.inputLogin, this.state.loginForm.inputPassword)
  }
  render() {
    const {errorText} = this.state.error
    const token = Cookies.get('token')
    if (token) return <Navigate to="/profile" replace={true} />
    return (
      <div>
        <div className='container'>
          <form className='row pt-5'>
            <div className="col-6 offset-3 mb-3 text-center mt-5"><img src={logo} style={{width: '200px', height: '200px'}} alt='logo'/></div>
            <div className="col-4 offset-4 mb-3 mt-5">
              <label htmlFor="inputLogin" className="form-label">Имя учётной записи</label>
              <input type="login" className="form-control" id="inputLogin" aria-describedby="emailHelp" onChange={this.handleSearchFormChange} />
            </div>
            <div className="col-4 offset-4 mb-3">
              <label htmlFor="inputPassword" className="form-label">Пароль</label>
              <input type="password" className="form-control" id="inputPassword" onChange={this.handleSearchFormChange} />
            </div>
            <div className='col-4 offset-4'>
              <div className="btn btn-primary" onClick={this.login}>Войти</div>
            </div>
            {errorText ? 
            <div className='col-4 offset-4'>
              <div className="alert alert-danger alert-dismissible fade show mt-3" role="alert">
                {errorText}
                <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            </div> : null}
          </form>
        </div>
      </div>
    );
  }
}  