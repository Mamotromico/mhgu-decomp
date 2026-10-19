extern "C" {

struct func_6122e120_layout {
    char pad0[4];
    int field_4;
    char pad8[4];
    int field_c;
};

int func_6122e120(const func_6122e120_layout *p) {
    return p->field_c - p->field_4;
}

}