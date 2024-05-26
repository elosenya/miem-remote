from django.db import models
from django.contrib.auth.models import User

import pymysql
from sshtunnel import SSHTunnelForwarder
from hashlib import sha256


# Create your models here.

class PnetModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=0)
    password = models.CharField(max_length=50, default="")
    admin = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        print(self.admin)
        role = 1
        if not self.admin:
            role = 1
        else:
            role = 0
        print(role)
        super(PnetModel, self).save(*args, **kwargs)
        print("Save", self.user, self.password)
        tunnel = SSHTunnelForwarder(('192.168.1.75', 22), ssh_password="pnet", ssh_username="root",
                                    remote_bind_address=("127.0.0.1", 3306))
        tunnel.start()
        conn = pymysql.connect(host='127.0.0.1', user='root', passwd='12345', db='pnetlab_db', port=tunnel.local_bind_port)
        cursor = conn.cursor()
        sql = "SELECT * FROM `users` WHERE `username` = %s"
        cursor.execute(sql, [self.user.__str__()])
        result = cursor.fetchall()
        print(result)
        if len(result) == 0:
            sql = """INSERT INTO `users` (`username`, `expiration`, `password`, `role`, `html5`, `offline`, `user_status`) 
            VALUES (%s, -1, %s, %s, 1, 1, 1);"""
            cursor.execute(sql, (self.user.__str__(), sha256(self.password.__str__().encode('utf-8')).hexdigest(), int(role)))
        else:
            sql = """UPDATE `users` set `password` = %s, `role` = %s where username = %s"""
            cursor.execute(sql, [sha256(self.password.__str__().encode('utf-8')).hexdigest(), int(role), self.user.__str__()])
        conn.commit()
        cursor.close()
        tunnel.stop()
