struct Data_6135a404 {
    unsigned char pad_0x00[0x40];
    unsigned int field_0x40;
    unsigned int field_0x44;
    unsigned int field_0x48;
    unsigned int field_0x4c;
};

extern "C" void func_6135a404(Data_6135a404 *p) {
    *(volatile unsigned int *)&p->field_0x40 = 0;
    *(volatile unsigned int *)&p->field_0x44 = 0;
    *(volatile unsigned int *)&p->field_0x48 = 0;
    *(volatile unsigned int *)&p->field_0x4c = 0;
}