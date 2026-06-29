# controladores/auditoriaservice.py
# servicio para registrar eventos de auditoria en la base de datos de forma centralizada

from modelos.usuario_model import UsuarioModel
from controladores.SecurityService import SecurityService

class AuditoriaService:
    @classmethod
    def registrar(cls, accion, objeto, valor_anterior=None, valor_nuevo=None):
        # obtener el nombre de usuario de la sesion activa o por defecto sistema
        usr = "sistema"
        usr_obj = SecurityService.get_usuario_actual()
        if usr_obj:
            usr = usr_obj.get("username", "sistema")
            
        try:
            model = UsuarioModel()
            model.registrar_auditoria(usr, accion, objeto, valor_anterior, valor_nuevo)
        except Exception as e:
            print(f"[DEBUG ERROR] falla al escribir log en auditoria: {e}")
