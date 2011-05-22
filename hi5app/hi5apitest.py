import tstatus2
from bitly_api import Connection
from oauthtwitter import OAuthApi
from twitter import Api
import oauth.oauth as oauth

C_KEY = "c1z2SA8p1EAXthvpCrYUA"
C_SECRET = "2Qh67Sf2I9iV13apPtdNXvQTwQ5NikJZRTjiQ9Gagac"
t1 = OAuthApi(C_KEY, C_SECRET)

r_token = t1.getRequestToken()
t2 = OAuthApi(C_KEY, C_SECRET, r_token)
a_token = t2.getAccessToken()
t = Api(C_KEY, C_SECRET, a_token)

b = Connection('acompa', 'R_9c2643b4c8c85a250493e90ce27a624d')
tstatus2.getHighFive(b, t, "achompas")
