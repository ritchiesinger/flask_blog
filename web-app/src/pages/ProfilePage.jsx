import React, {Component} from 'react'
import { Navigate } from "react-router-dom";
import Header from '../components/Header'
import Footer from '../components/Footer'
import { getProfile } from '../api/Api'
import Cookies from 'js-cookie'
import userLogo from '../assets/user.png'


export default class ProfilePage extends Component {
  constructor(props) {
    super(props)
    this.state = {
      loading: {},
      error: {errorCode: null, errorText: null},
      profile: {login: null, id: null, roles: []}
    }
  }
  componentDidMount = () => {
      const token = Cookies.get('token')
      getProfile(this, token)
  }
  render() {
    const {profile} = this.state
    const token = Cookies.get('token')
    if (token === undefined) return <Navigate to="/login" replace={true} />
    return (
      <div>
        <Header user={profile} parentComponent={this} activePage='profile' />
        <div className='container' style={{minHeight: 'calc(100vh - 116px)'}}>
          <div className='row'>
            <div className="col-6 offset-3 mb-3 text-center mt-5"><img src={userLogo} style={{width: '200px', height: '200px'}} alt="Аватар"/></div>
            <div className="col-6 offset-3 text-center fs-2">{profile.login}</div>
            <div className="col-6 offset-3 text-center mt-2"><strong>email:&nbsp;</strong><span>{profile.email}</span>&nbsp;&nbsp;<button className='font-weight-bold text-light btn btn-primary btn-sm'>Изменить</button></div>
            <div className="col-6 offset-3 text-center fs-3 mt-3">Роли</div>
            {profile.roles.map((role, index) => (
              <div key={`roleRow-${index}`} className='col-6 offset-3 text-center'><strong>{role}</strong></div>
            ))}
          </div>
        </div>
        <Footer />
      </div>
    );
  }
}  