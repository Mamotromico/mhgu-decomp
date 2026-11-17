extern "C" void func_61370708(void);

namespace nn { namespace os { void YieldThread(void); } }

extern "C" void func_61370708(void) {
    nn::os::YieldThread();
}