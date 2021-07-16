import os, requests, json

from config import Config

class AuthApi():
    API_ENDPOINT = f'{Config.API_HOSTNAME}/auth'
    TOKEN_PATH = os.path.join(Config.documents_path, 'access-token.json')

    @classmethod
    def CheckJWT(cls):
        if os.path.exists(cls.TOKEN_PATH):
            with open(cls.TOKEN_PATH, 'r') as fp:
                obj = json.load(fp)
            
            if 'access-token' in obj:
                url = f'{cls.API_ENDPOINT}/jwt'
                headers = {'Authorization': f'Bearer {obj["access-token"]}'}
                res = requests.get(url, headers=headers)
                body = json.loads(res.content)
                
                if 'username' in body:
                    return body['username']
                else:
                    # delete token's file if authentication failed
                    cls.DeleteToken()
        return False

    @classmethod
    def DeleteToken(cls):
        '''
        delete token file, located in: `{Config.documents_path}/access-token.json`
        '''
        try:
            if os.path.exists(cls.TOKEN_PATH):
                os.remove(cls.TOKEN_PATH)
            return True
        except:
            return False

    @classmethod
    def Login(cls, username, password, save_jwt=True):
        url = f'{cls.API_ENDPOINT}/users'
        body = {
            'username': username,
            'password': password
        }
        
        res = requests.get(url, body)
        body = json.loads(res.content)
        if 'access-token' in body:
            if save_jwt:
                os.makedirs(Config.documents_path, exist_ok=True)
                with open(cls.TOKEN_PATH, 'w') as fp:
                    json.dump(body, fp)
            return True
        return False
    
    @classmethod
    def Register(cls, username, password):
        url = f'{AuthApi.API_ENDPOINT}/users'
        pass
