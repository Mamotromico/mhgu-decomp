extern "C" struct S { char pad[0x9c]; };
extern "C" void func_607cc110(S*);

extern "C" void func_601c8b00(char *p) {
    func_607cc110((S*)(p + 0x9c));
}