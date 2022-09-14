import React, {Component} from 'react'
import { Navigate, Link } from "react-router-dom"
import getToken from '../api/Api'
import Cookies from 'js-cookie'
import logo from '../assets/reactLogo.png'
import logoCSS from './logo.css'  // eslint-disable-line no-unused-vars
import Footer from '../components/Footer'

export default class LoginPage extends Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: false,
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
    const token = Cookies.get('token')
    const {props, state} = this
    const {error, loading, loginForm} = state
    const {errorText} = error
    const {inputLogin, inputPassword} = loginForm
    const {singIn} = props
    if (token) return <Navigate to="/profile" replace={true} />
    return (
      <div>
        <div className='container' style={{minHeight: 'calc(100vh - 58px)'}}>
          <form className='row pt-5'>
            <div className="col-6 offset-3 mb-3 text-center mt-5"><img className={loading ? 'rotate' : ''} src={logo} style={{width: '200px', height: '200px'}} alt='logo'/></div>
            <div className="col-4 offset-4 mb-3 mt-5">
              <label htmlFor="inputLogin" className="form-label">Имя учётной записи <span className='text-danger'>*</span></label>
              <input type="login" className="form-control" id="inputLogin" aria-describedby="emailHelp" onChange={this.handleSearchFormChange} readOnly={loading}/>
            </div>
            <div className="col-4 offset-4 mb-3">
              <label htmlFor="inputPassword" className="form-label">Пароль <span className='text-danger'>*</span></label>
              <input type="password" className="form-control" id="inputPassword" onChange={this.handleSearchFormChange} readOnly={loading}/>
            </div>
            <div className='col-4 offset-4'>
              <button 
                className="btn btn-primary" 
                onClick={loading ? () => {} : this.login} 
                disabled={loading || inputLogin === "" || inputPassword === ""}>
                  {loading ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" /> : null}
                  {loading ? <span>&nbsp;&nbsp;Загрузка</span> : <span>Войти</span>}
              </button>
              <Link to='/registration' onClick={loading ? e => e.preventDefault() : ()=>{}}><div className={`btn link-${loading ? 'secondary' : 'primary'}`}>Создать профиль</div></Link>
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
        <Footer />
      </div>
    );
  }
}  