from django.db import models

class Cita(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    fecha = models.DateField()
    hora = models.CharField(max_length=20)
    servicio = models.CharField(max_length=150)
    precio_total = models.DecimalField(max_digits=8, decimal_places=2)
    adelanto_pagado = models.DecimalField(max_digits=8, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pago = models.CharField(max_length=50)
    codigo_operacion = models.CharField(max_length=50)
    estado = models.CharField(max_length=50, default="50% Pagado")
    hora_inicio_real = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.fecha} {self.hora}"