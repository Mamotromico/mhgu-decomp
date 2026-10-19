struct Data_6122e648 {
    unsigned char pad0[0x110];
    unsigned char field_0x110;
    unsigned char pad1[2];
    unsigned char field_0x113;
};

extern "C" void func_6122e648(Data_6122e648* p) {
    p->field_0x110 = 1;
    p->field_0x113 = 1;
}