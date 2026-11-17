extern "C" {

struct elem_60c46c70 {
    char pad0[0x10];
    void *field_0x10;
};

struct obj_60c46c70 {
    char pad0[0xbc];
    unsigned int field_0xbc;
    char pad1[0xc8 - 0xbc - 4];
    elem_60c46c70 **field_0xc8;
};

void func_60c46c70(obj_60c46c70 *self, unsigned int idx, void *val) {
    if (idx != 0xffffffffu && self->field_0xbc > idx) {
        elem_60c46c70 *e = self->field_0xc8[idx];
        if (e != 0) {
            e->field_0x10 = val;
        }
    }
}

}