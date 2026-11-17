extern "C" void func_610622dc(unsigned char *p) {
    unsigned char v = *(unsigned char *)(p + 0xb5f5);
    unsigned r2a = (v == 4) ? 0x165 : 0x161;
    *(unsigned *)(p + 0xcae0) = r2a;
    unsigned r2b = (v == 4) ? 0x168 : 0x163;
    *(unsigned *)(p + 0xcae4) = r2b;
    unsigned r2c = (v == 4) ? 0x16a : 0x164;
    *(unsigned *)(p + 0xcae8) = r2c;
}