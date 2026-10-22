struct T600af598 {
    unsigned char pad_0[0x3DC];
    void (*field_3DC)(void *);
};

struct S600af598 {
    T600af598 *field_0;
    unsigned char pad_4[0x73E1 - 4];
    unsigned char field_73E1;
};

extern "C" void func_600af598(S600af598 *self) {
    if (self->field_73E1 >= 3)
        self->field_0->field_3DC(self);
}