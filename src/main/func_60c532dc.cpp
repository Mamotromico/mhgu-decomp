struct Func60c532dcStruct {
    unsigned char pad[0xc0];
    unsigned int field;
};

extern "C" void func_60c532dc(Func60c532dcStruct* p) {
    p->field ^= 1u;
}