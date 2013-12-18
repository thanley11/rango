from oauth2client.client import OAuth2WebServerFlow

def main():
FLOW = OAuth2WebServerFlow(
		client_id='62372255716-9mhkq9qpouocv6hntf5fktbr236fgctn.apps.googleusercontent.com'
		client_secret='IT_qM-x1VwOQbz0oedyzG-Hy',
		redirect_uri='https://google.com',
		scope='https://www.googleapis.com/auth/appssearch')

if __name__ == '__main__':
  main()
