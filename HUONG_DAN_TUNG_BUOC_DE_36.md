# HƯỚNG DẪN TỪNG BƯỚC XÂY DỰNG DAPP — ĐỀ 36: TOUR RESERVATION DAPP

Tài liệu này hướng dẫn bạn tự tay xây dựng hoàn chỉnh **Tour Reservation DApp** theo từng bước (giống cấu trúc các bài Lab trên VS Code), gồm:

- **Phần 1:** Viết và Deploy Smart Contract Solidity (`TourReservation.sol`)
- **Phần 2:** Tạo dự án Frontend bằng **React + Vite + `web3.js`** trong VS Code
- **Phần 3:** Viết code từng file cho Frontend và kết nối Web3 với MetaMask
- **Phần 4:** Chạy thử và kiểm tra đầy đủ các yêu cầu nghiệp vụ

---

## Yêu cầu đề bài (Đề 36)

Công ty du lịch mở tour **25 chỗ** với giá **0,08 ETH/người**; khách đặt chỗ trước.

- **Các hàm bắt buộc trên Smart Contract:**
  - `createTour()`
  - `bookSeats()`
  - `getAvailableSeats()`
  - `getMyBookings()`
- **Yêu cầu nghiệp vụ:**
  1. Chỉ điều hành (`operator`) mới được tạo tour với số chỗ nguyên dương.
  2. Số chỗ đặt phải là số nguyên dương, không vượt quá số chỗ trống và phải thanh toán đúng phí (`số chỗ × giá vé`).
  3. Cập nhật đúng số chỗ trống và số chỗ đã đặt theo từng địa chỉ ví.
  4. Giao diện hiển thị giá tour, chỗ trống còn lại và vé đã đặt của ví đang kết nối.

---

## PHẦN 1: TẠO & DEPLOY SMART CONTRACT SOLIDITY

> Bạn có thể dùng **Remix IDE** (trên trình duyệt, nhanh nhất để học từng bước) kết hợp với ví **MetaMask** (mạng **Sepolia Testnet** hoặc **Localhost**).

### Bước 1.1: Tạo file Smart Contract

1. Mở [https://remix.ethereum.org](https://remix.ethereum.org).
2. Trong thư mục `contracts/`, tạo file mới tên **`TourReservation.sol`**.
3. Dán toàn bộ code Solidity sau vào file:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TourReservation {
    address public operator;
    uint256 public totalSeats;
    uint256 public availableSeats;
    uint256 public ticketPrice; // Đơn vị: wei (0.08 ETH = 80000000000000000 wei)
    bool public isTourActive;

    // Lưu số vé đã đặt theo từng địa chỉ ví
    mapping(address => uint256) private bookings;

    event TourCreated(uint256 totalSeats, uint256 ticketPrice);
    event SeatsBooked(address indexed customer, uint256 seats, uint256 totalPaid);

    modifier onlyOperator() {
        require(msg.sender == operator, "Chi dieu hanh moi co quyen thuc hien");
        _;
    }

    constructor() {
        operator = msg.sender;
    }

    // 1. Chỉ điều hành tạo tour với số chỗ dương và giá vé dương
    function createTour(uint256 _totalSeats, uint256 _ticketPrice) external onlyOperator {
        require(_totalSeats > 0, "So cho phai lon hon 0");
        require(_ticketPrice > 0, "Gia ve phai lon hon 0");

        totalSeats = _totalSeats;
        availableSeats = _totalSeats;
        ticketPrice = _ticketPrice;
        isTourActive = true;

        emit TourCreated(_totalSeats, _ticketPrice);
    }

    // 2. Khách hàng đặt chỗ: nguyên dương, không vượt chỗ trống, thanh toán đúng phí
    function bookSeats(uint256 _seats) external payable {
        require(isTourActive, "Hien chua co tour nao duoc mo");
        require(_seats > 0, "So cho dat phai lon hon 0");
        require(_seats <= availableSeats, "Khong du cho trong");
        require(msg.value == _seats * ticketPrice, "Thanh toan khong dung phi");

        availableSeats -= _seats;
        bookings[msg.sender] += _seats;

        emit SeatsBooked(msg.sender, _seats, msg.value);
    }

    // 3. Xem số chỗ trống còn lại
    function getAvailableSeats() external view returns (uint256) {
        return availableSeats;
    }

    // 4. Xem số vé đã đặt của ví đang gọi
    function getMyBookings() external view returns (uint256) {
        return bookings[msg.sender];
    }
}
```

### Bước 1.2: Compile (Biên dịch) và lấy ABI

1. Ở thanh công cụ bên trái Remix, chọn tab **Solidity Compiler** (biểu tượng chữ S).
2. Chọn Compiler phiên bản **`0.8.20`** (hoặc `0.8.x` >= `0.8.20`).
3. Nhấn **Compile TourReservation.sol**.
4. Sau khi compile thành công (có dấu tick xanh), kéo xuống dưới cùng tab Compiler và nhấn **ABI** để copy (hoặc lưu lại dùng cho Phần 3).
5. [
   {
   "inputs": [],
   "stateMutability": "nonpayable",
   "type": "constructor"
   },
   {
   "anonymous": false,
   "inputs": [
   {
   "indexed": true,
   "internalType": "address",
   "name": "customer",
   "type": "address"
   },
   {
   "indexed": false,
   "internalType": "uint256",
   "name": "seats",
   "type": "uint256"
   },
   {
   "indexed": false,
   "internalType": "uint256",
   "name": "totalPaid",
   "type": "uint256"
   }
   ],
   "name": "SeatsBooked",
   "type": "event"
   },
   {
   "anonymous": false,
   "inputs": [
   {
   "indexed": false,
   "internalType": "uint256",
   "name": "totalSeats",
   "type": "uint256"
   },
   {
   "indexed": false,
   "internalType": "uint256",
   "name": "ticketPrice",
   "type": "uint256"
   }
   ],
   "name": "TourCreated",
   "type": "event"
   },
   {
   "inputs": [],
   "name": "availableSeats",
   "outputs": [
   {
   "internalType": "uint256",
   "name": "",
   "type": "uint256"
   }
   ],
   "stateMutability": "view",
   "type": "function"
   },
   {
   "inputs": [
   {
   "internalType": "uint256",
   "name": "_seats",
   "type": "uint256"
   }
   ],
   "name": "bookSeats",
   "outputs": [],
   "stateMutability": "payable",
   "type": "function"
   },
   {
   "inputs": [
   {
   "internalType": "uint256",
   "name": "_totalSeats",
   "type": "uint256"
   },
   {
   "internalType": "uint256",
   "name": "_ticketPrice",
   "type": "uint256"
   }
   ],
   "name": "createTour",
   "outputs": [],
   "stateMutability": "nonpayable",
   "type": "function"
   },
   {
   "inputs": [],
   "name": "getAvailableSeats",
   "outputs": [
   {
   "internalType": "uint256",
   "name": "",
   "type": "uint256"
   }
   ],
   "stateMutability": "view",
   "type": "function"
   },
   {
   "inputs": [],
   "name": "getMyBookings",
   "outputs": [
   {
   "internalType": "uint256",
   "name": "",
   "type": "uint256"
   }
   ],
   "stateMutability": "view",
   "type": "function"
   },
   {
   "inputs": [],
   "name": "isTourActive",
   "outputs": [
   {
   "internalType": "bool",
   "name": "",
   "type": "bool"
   }
   ],
   "stateMutability": "view",
   "type": "function"
   },
   {
   "inputs": [],
   "name": "operator",
   "outputs": [
   {
   "internalType": "address",
   "name": "",
   "type": "address"
   }
   ],
   "stateMutability": "view",
   "type": "function"
   },
   {
   "inputs": [],
   "name": "ticketPrice",
   "outputs": [
   {
   "internalType": "uint256",
   "name": "",
   "type": "uint256"
   }
   ],
   "stateMutability": "view",
   "type": "function"
   },
   {
   "inputs": [],
   "name": "totalSeats",
   "outputs": [
   {
   "internalType": "uint256",
   "name": "",
   "type": "uint256"
   }
   ],
   "stateMutability": "view",
   "type": "function"
   }
   ]

### Bước 1.3: Deploy (Triển khai) và lấy Contract Address

1. Chọn tab **Deploy & Run Transactions** (biểu tượng Ethereum).
2. Ở mục **Environment**:
   - Chọn **Injected Provider - MetaMask** (nếu deploy lên Sepolia Testnet hoặc Hardhat Local qua MetaMask).
   - *(Lưu ý: Không dùng Remix VM khi test cùng React + MetaMask, vì MetaMask trên trình duyệt không thể gọi vào Remix VM).*
3. Nhấn **Deploy** và xác nhận giao dịch trên MetaMask.
4. Sau khi deploy xong, nhìn xuống mục **Deployed Contracts**:
   - Copy **Contract Address** (dạng `0x...`).
   - 0xd9145CCE52D386f254917e481eB44e9943F39138
   - Test thử hàm `createTour` bằng cách nhập:
     - `_totalSeats`: `25`
     - `_ticketPrice`: `80000000000000000` (tức `0.08 ETH` tính theo wei)
   - Nhấn **transact** và xác nhận trên MetaMask.

---

## PHẦN 2: TẠO DỰ ÁN FRONTEND TRONG VS CODE

### Bước 2.1: Khởi tạo dự án React + Vite

1. Mở **VS Code** → **Terminal** → **New Terminal**.
2. Di chuyển vào thư mục chứa đồ án của bạn và chạy lệnh tạo dự án:

```bash
npm create vite@latest frontend -- --template react
```

*(Nếu được hỏi cài `create-vite` → nhấn `y` + Enter. Nếu hỏi chọn linter/tự cài → chọn mặc định hoặc `No` để tự cài bên dưới).*

3. Di chuyển vào thư mục `frontend` và cài các thư viện cần thiết (`react` và `web3`):

```bash
cd frontend
npm install
npm install web3
```

4. Mở thư mục `frontend` trong VS Code (**File → Open Folder → chọn `frontend`**).

### Bước 2.2: Cấu trúc thư mục cần có

Trong `frontend`, bạn sẽ làm việc với cấu trúc sau:

```text
frontend/
├── index.html
├── package.json
└── src/
    ├── config/
    │   └── contract.js        <-- (Tạo mới) Lưu Contract Address & ABI
    ├── utils/
    │   └── web3Client.js      <-- (Tạo mới) Kết nối MetaMask bằng web3.js
    ├── App.jsx                <-- (Chỉnh sửa) Giao diện & logic gọi DApp
    ├── App.css                <-- (Chỉnh sửa) CSS trang trí giao diện
    ├── index.css              <-- (Chỉnh sửa) CSS nền mặc định
    └── main.jsx               <-- (Giữ nguyên)
```

---

## PHẦN 3: VIẾT CODE TỪNG FILE CHO FRONTEND

### Bước 3.1: Chỉnh sửa file `index.html`

Mở `index.html`, sửa thẻ `<title>` thành tiêu đề DApp:

```html
<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Tour Reservation DApp - Đề 36</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### Bước 3.2: Tạo file `src/config/contract.js`

Tạo thư mục `src/config` và file `contract.js`. Dán đoạn code sau và **thay `CONTRACT_ADDRESS`** bằng địa chỉ bạn đã deploy ở **Bước 1.3**:

```javascript
// Dán địa chỉ Smart Contract bạn vừa deploy vào đây (ví dụ: "0x1234...")
export const CONTRACT_ADDRESS = "0xd9145CCE52D386f254917e481eB44e9943F39138";

export const TOUR_DEFAULT = {
  name: "Tour Du Lịch Khám Phá 25 Chỗ",
  totalSeats: 25,
  ticketPriceEth: "0.08",
};

// ABI khớp với TourReservation.sol
export const CONTRACT_ABI = [
  {
    inputs: [],
    name: "operator",
    outputs: [{ internalType: "address", name: "", type: "address" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "ticketPrice",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "totalSeats",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [
      { internalType: "uint256", name: "_totalSeats", type: "uint256" },
      { internalType: "uint256", name: "_ticketPrice", type: "uint256" },
    ],
    name: "createTour",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
  {
    inputs: [{ internalType: "uint256", name: "_seats", type: "uint256" }],
    name: "bookSeats",
    outputs: [],
    stateMutability: "payable",
    type: "function",
  },
  {
    inputs: [],
    name: "getAvailableSeats",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "getMyBookings",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
];
```

### Bước 3.3: Tạo file `src/utils/web3Client.js`

Tạo thư mục `src/utils` và file `web3Client.js`. File này đóng gói các hàm kết nối MetaMask bằng `web3.js`:

```javascript
import Web3 from "web3";
import { CONTRACT_ABI, CONTRACT_ADDRESS } from "../config/contract";

export function hasMetaMask() {
  return typeof window !== "undefined" && typeof window.ethereum !== "undefined";
}

export function createWeb3Instance() {
  if (!hasMetaMask()) {
    throw new Error("Chưa phát hiện ví MetaMask. Vui lòng cài đặt MetaMask extension.");
  }
  return new Web3(window.ethereum);
}

export async function connectMetaMaskWallet() {
  const web3 = createWeb3Instance();
  const accounts = await window.ethereum.request({
    method: "eth_requestAccounts",
  });

  if (!accounts || accounts.length === 0) {
    throw new Error("Không tìm thấy tài khoản ví nào được chọn.");
  }

  const account = accounts[0];
  const balanceWei = await web3.eth.getBalance(account);
  const balanceEth = Number(web3.utils.fromWei(balanceWei, "ether")).toFixed(4);
  const chainId = Number(await web3.eth.getChainId());

  return { web3, account, balanceEth, chainId };
}

export async function getWalletSnapshot(web3, account) {
  const balanceWei = await web3.eth.getBalance(account);
  const balanceEth = Number(web3.utils.fromWei(balanceWei, "ether")).toFixed(4);
  const chainId = Number(await web3.eth.getChainId());
  return { balanceEth, chainId };
}

export function getTourContract(web3) {
  if (!CONTRACT_ADDRESS) return null;
  return new web3.eth.Contract(CONTRACT_ABI, CONTRACT_ADDRESS);
}

export function formatShortAddress(address) {
  if (!address) return "";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export function getNetworkName(chainId) {
  const networks = {
    1: "Ethereum Mainnet",
    11155111: "Sepolia Testnet",
    31337: "Hardhat Local",
    1337: "Localhost 8545",
  };
  return networks[chainId] || `Chain ID: ${chainId}`;
}
```

### Bước 3.4: Viết giao diện chính trong `src/App.jsx`

Mở `src/App.jsx`, xóa toàn bộ nội dung cũ và dán code sau:

```jsx
import { useEffect, useState } from "react";
import { CONTRACT_ADDRESS, TOUR_DEFAULT } from "./config/contract";
import {
  connectMetaMaskWallet,
  createWeb3Instance,
  formatShortAddress,
  getNetworkName,
  getTourContract,
  getWalletSnapshot,
  hasMetaMask,
} from "./utils/web3Client";
import "./App.css";

function App() {
  const isOnChainMode = Boolean(CONTRACT_ADDRESS);

  const [web3, setWeb3] = useState(null);
  const [account, setAccount] = useState("");
  const [balanceEth, setBalanceEth] = useState("0.0000");
  const [chainId, setChainId] = useState(null);

  const [operatorAddress, setOperatorAddress] = useState("");
  const [totalSeats, setTotalSeats] = useState(TOUR_DEFAULT.totalSeats);
  const [availableSeats, setAvailableSeats] = useState(TOUR_DEFAULT.totalSeats);
  const [ticketPriceEth, setTicketPriceEth] = useState(TOUR_DEFAULT.ticketPriceEth);
  const [tourCreated, setTourCreated] = useState(true);

  const [mockBookingsByWallet, setMockBookingsByWallet] = useState({});
  const [myBookings, setMyBookings] = useState(0);

  const [seatsToBook, setSeatsToBook] = useState("1");
  const [newTourSeats, setNewTourSeats] = useState(String(TOUR_DEFAULT.totalSeats));
  const [newTourPrice, setNewTourPrice] = useState(TOUR_DEFAULT.ticketPriceEth);

  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  const showStatus = (type, text) => setStatusMessage({ type, text });

  const isOperator =
    account &&
    operatorAddress &&
    account.toLowerCase() === operatorAddress.toLowerCase();

  const syncOnChainData = async (web3Instance, activeAccount) => {
    const contract = getTourContract(web3Instance);
    if (!contract) return;

    const [op, priceWei, total, avail, booked] = await Promise.all([
      contract.methods.operator().call(),
      contract.methods.ticketPrice().call(),
      contract.methods.totalSeats().call(),
      contract.methods.getAvailableSeats().call(),
      contract.methods.getMyBookings().call({ from: activeAccount }),
    ]);

    setOperatorAddress(op);
    setTicketPriceEth(web3Instance.utils.fromWei(priceWei, "ether"));
    setTotalSeats(Number(total));
    setAvailableSeats(Number(avail));
    setMyBookings(Number(booked));
    setTourCreated(Number(total) > 0);
  };

  useEffect(() => {
    if (!isOnChainMode && account) {
      setMyBookings(mockBookingsByWallet[account.toLowerCase()] || 0);
    } else if (!account) {
      setMyBookings(0);
    }
  }, [account, isOnChainMode, mockBookingsByWallet]);

  useEffect(() => {
    if (!hasMetaMask()) return;

    const handleAccountsChanged = async (accounts) => {
      if (!accounts || accounts.length === 0) {
        setAccount("");
        setBalanceEth("0.0000");
        setMyBookings(0);
        showStatus("info", "Ví MetaMask đã ngắt kết nối.");
        return;
      }

      const nextAccount = accounts[0];
      setAccount(nextAccount);

      try {
        const w3 = web3 || createWeb3Instance();
        setWeb3(w3);
        const snapshot = await getWalletSnapshot(w3, nextAccount);
        setBalanceEth(snapshot.balanceEth);
        setChainId(snapshot.chainId);

        if (isOnChainMode) {
          await syncOnChainData(w3, nextAccount);
        }
      } catch (err) {
        showStatus("error", err.message);
      }
    };

    const handleChainChanged = () => window.location.reload();

    window.ethereum.on("accountsChanged", handleAccountsChanged);
    window.ethereum.on("chainChanged", handleChainChanged);

    return () => {
      window.ethereum.removeListener("accountsChanged", handleAccountsChanged);
      window.ethereum.removeListener("chainChanged", handleChainChanged);
    };
  }, [web3, isOnChainMode]);

  const handleConnectWallet = async () => {
    setLoading(true);
    try {
      const { web3: w3, account: acc, balanceEth: bal, chainId: netId } =
        await connectMetaMaskWallet();

      setWeb3(w3);
      setAccount(acc);
      setBalanceEth(bal);
      setChainId(netId);

      if (!isOnChainMode && !operatorAddress) {
        setOperatorAddress(acc);
      }

      if (isOnChainMode) {
        await syncOnChainData(w3, acc);
      }

      showStatus("success", `Đã kết nối ví ${formatShortAddress(acc)} thành công!`);
    } catch (err) {
      showStatus("error", err.message || "Không thể kết nối MetaMask.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTour = async (e) => {
    e.preventDefault();
    if (!account) return showStatus("error", "Vui lòng kết nối ví MetaMask trước.");

    const seatsNum = Number(newTourSeats);
    const priceNum = Number(newTourPrice);

    if (!Number.isInteger(seatsNum) || seatsNum <= 0) {
      return showStatus("error", "Số chỗ của tour phải là số nguyên dương (> 0).");
    }
    if (Number.isNaN(priceNum) || priceNum <= 0) {
      return showStatus("error", "Giá vé tour phải lớn hơn 0 ETH.");
    }
    if (!isOperator) {
      return showStatus("error", "Chỉ ví Điều hành (Operator) mới có quyền tạo tour.");
    }

    setLoading(true);
    try {
      if (isOnChainMode) {
        const contract = getTourContract(web3);
        const priceWei = web3.utils.toWei(String(newTourPrice), "ether");
        await contract.methods.createTour(seatsNum, priceWei).send({ from: account });
        await syncOnChainData(web3, account);
      } else {
        setTotalSeats(seatsNum);
        setAvailableSeats(seatsNum);
        setTicketPriceEth(String(priceNum));
        setMockBookingsByWallet({});
        setMyBookings(0);
        setTourCreated(true);
      }
      showStatus("success", `Đã mở tour mới với ${seatsNum} chỗ, giá ${priceNum} ETH/người!`);
    } catch (err) {
      showStatus("error", err.message || "Tạo tour thất bại.");
    } finally {
      setLoading(false);
    }
  };

  const handleBookSeats = async (e) => {
    e.preventDefault();
    if (!account) return showStatus("error", "Vui lòng kết nối ví MetaMask trước khi đặt chỗ.");
    if (!tourCreated) return showStatus("error", "Hiện chưa có tour nào được mở.");

    const seatsNum = Number(seatsToBook);
    if (!Number.isInteger(seatsNum) || seatsNum <= 0) {
      return showStatus("error", "Số chỗ đặt phải là số nguyên dương (> 0).");
    }
    if (seatsNum > availableSeats) {
      return showStatus(
        "error",
        `Số chỗ đặt (${seatsNum}) vượt quá số chỗ trống còn lại (${availableSeats}).`
      );
    }

    const totalCostEth = (seatsNum * Number(ticketPriceEth)).toFixed(4);

    setLoading(true);
    try {
      if (isOnChainMode) {
        const contract = getTourContract(web3);
        const priceWei = BigInt(web3.utils.toWei(String(ticketPriceEth), "ether"));
        const valueWei = (priceWei * BigInt(seatsNum)).toString();

        await contract.methods.bookSeats(seatsNum).send({
          from: account,
          value: valueWei,
        });

        const snapshot = await getWalletSnapshot(web3, account);
        setBalanceEth(snapshot.balanceEth);
        await syncOnChainData(web3, account);
      } else {
        setAvailableSeats((prev) => prev - seatsNum);
        const key = account.toLowerCase();
        setMockBookingsByWallet((prev) => ({
          ...prev,
          [key]: (prev[key] || 0) + seatsNum,
        }));
      }

      showStatus("success", `Đặt thành công ${seatsNum} chỗ (Thanh toán ${totalCostEth} ETH)!`);
    } catch (err) {
      showStatus("error", err.message || "Đặt chỗ thất bại.");
    } finally {
      setLoading(false);
    }
  };

  const calculatedTotalEth =
    Number(seatsToBook) > 0 && Number.isInteger(Number(seatsToBook))
      ? (Number(seatsToBook) * Number(ticketPriceEth)).toFixed(4)
      : "0.0000";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-badge">Đề 36</span>
          <div>
            <h1>Tour Reservation DApp</h1>
            <p className="subtitle">Đặt vé du lịch minh bạch trên Web3 & Solidity</p>
          </div>
        </div>

        <div className="wallet-area">
          {account ? (
            <div className="wallet-pill">
              <span className={`role-tag ${isOperator ? "operator" : "customer"}`}>
                {isOperator ? "Điều hành" : "Khách hàng"}
              </span>
              <span className="network-tag">{getNetworkName(chainId)}</span>
              <span className="balance-tag">{balanceEth} ETH</span>
              <span className="address-tag" title={account}>
                {formatShortAddress(account)}
              </span>
            </div>
          ) : (
            <button className="btn btn-primary" onClick={handleConnectWallet} disabled={loading}>
              {loading ? "Đang kết nối..." : "Kết nối MetaMask"}
            </button>
          )}
        </div>
      </header>

      <main className="container">
        <div className={`mode-banner ${isOnChainMode ? "onchain" : "mock"}`}>
          {isOnChainMode ? (
            <>
              <strong>Chế độ On-Chain:</strong> Đang kết nối Smart Contract tại{" "}
              <code>{formatShortAddress(CONTRACT_ADDRESS)}</code>
            </>
          ) : (
            <>
              <strong>Chế độ mô phỏng:</strong> Chưa có <code>CONTRACT_ADDRESS</code>.
            </>
          )}
        </div>

        {statusMessage && (
          <div className={`alert alert-${statusMessage.type}`}>
            <span>{statusMessage.text}</span>
            <button className="alert-close" onClick={() => setStatusMessage(null)}>
              ×
            </button>
          </div>
        )}

        <section className="stats-grid">
          <div className="stat-card">
            <span className="stat-label">Giá vé / người</span>
            <strong className="stat-value">{ticketPriceEth} ETH</strong>
            <span className="stat-hint">Thanh toán đúng phí khi đặt</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">Chỗ trống còn lại</span>
            <strong className="stat-value accent">
              {availableSeats} / {totalSeats}
            </strong>
            <span className="stat-hint">Hàm: getAvailableSeats()</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">Vé bạn đã đặt</span>
            <strong className="stat-value">{myBookings} chỗ</strong>
            <span className="stat-hint">Hàm: getMyBookings()</span>
          </div>
        </section>

        <section className="panels-grid">
          <div className="panel">
            <div className="panel-header">
              <h2>Đặt chỗ Tour</h2>
              <span className="fn-chip">bookSeats()</span>
            </div>
            <p className="panel-desc">{TOUR_DEFAULT.name}</p>

            <form onSubmit={handleBookSeats} className="form-stack">
              <label className="field">
                <span>Số lượng chỗ muốn đặt</span>
                <input
                  type="number"
                  min="1"
                  max={availableSeats || 1}
                  step="1"
                  value={seatsToBook}
                  onChange={(e) => setSeatsToBook(e.target.value)}
                  required
                />
              </label>

              <div className="summary-row">
                <span>Tổng thanh toán dự kiến:</span>
                <strong>{calculatedTotalEth} ETH</strong>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-full"
                disabled={loading || !account || availableSeats === 0}
              >
                {availableSeats === 0 ? "Tour đã hết chỗ" : loading ? "Đang xử lý..." : "Đặt chỗ ngay"}
              </button>
            </form>
          </div>

          <div className="panel">
            <div className="panel-header">
              <h2>Quản lý Điều hành</h2>
              <span className="fn-chip">createTour()</span>
            </div>
            <p className="panel-desc">
              {operatorAddress ? (
                <>
                  Ví điều hành: <code>{formatShortAddress(operatorAddress)}</code>
                </>
              ) : (
                "Kết nối ví để kiểm tra quyền điều hành."
              )}
            </p>

            <form onSubmit={handleCreateTour} className="form-stack">
              <label className="field">
                <span>Tổng số chỗ (nguyên dương)</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={newTourSeats}
                  onChange={(e) => setNewTourSeats(e.target.value)}
                  required
                />
              </label>

              <label className="field">
                <span>Giá vé mỗi người (ETH)</span>
                <input
                  type="number"
                  min="0.0001"
                  step="any"
                  value={newTourPrice}
                  onChange={(e) => setNewTourPrice(e.target.value)}
                  required
                />
              </label>

              <button
                type="submit"
                className="btn btn-secondary btn-full"
                disabled={loading || !account || !isOperator}
              >
                {!account
                  ? "Cần kết nối ví"
                  : !isOperator
                  ? "Chỉ Điều hành được tạo tour"
                  : "Tạo / Mở lại Tour"}
              </button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
```

### Bước 3.5: Trang trí giao diện với `src/index.css` và `src/App.css`

1. Mở `src/index.css`, xóa nội dung cũ và dán:

```css
:root {
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #0f172a;
  background-color: #f1f5f9;
  line-height: 1.5;
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; }
code {
  font-family: ui-monospace, monospace;
  background: rgba(15, 23, 42, 0.07);
  padding: 0.12rem 0.4rem;
  border-radius: 6px;
  font-size: 0.88em;
}
```

2. Mở `src/App.css`, xóa nội dung cũ và dán:

```css
.app-shell { min-height: 100vh; display: flex; flex-direction: column; }
.topbar {
  background: #fff; border-bottom: 1px solid #e2e8f0; padding: 1rem 2rem;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
}
.brand { display: flex; align-items: center; gap: 0.85rem; }
.brand-badge { background: #2563eb; color: #fff; font-weight: 700; font-size: 0.85rem; padding: 0.35rem 0.7rem; border-radius: 8px; }
.brand h1 { margin: 0; font-size: 1.25rem; }
.subtitle { margin: 0; font-size: 0.85rem; color: #64748b; }
.wallet-pill {
  display: flex; align-items: center; gap: 0.5rem; background: #f8fafc;
  border: 1px solid #cbd5e1; padding: 0.4rem 0.75rem; border-radius: 999px; font-size: 0.85rem; flex-wrap: wrap;
}
.role-tag { font-weight: 600; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.78rem; }
.role-tag.operator { background: #fef3c7; color: #92400e; }
.role-tag.customer { background: #dbeafe; color: #1e40af; }
.balance-tag { font-weight: 600; color: #0f766e; }
.address-tag { font-family: ui-monospace, monospace; font-weight: 600; }
.container { width: 100%; max-width: 980px; margin: 2rem auto; padding: 0 1.25rem; display: flex; flex-direction: column; gap: 1.5rem; }
.mode-banner { padding: 0.85rem 1.1rem; border-radius: 12px; font-size: 0.9rem; border: 1px solid; }
.mode-banner.mock { background: #eff6ff; border-color: #bfdbfe; color: #1e3a8a; }
.mode-banner.onchain { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
.alert { display: flex; align-items: center; justify-content: space-between; padding: 0.85rem 1.1rem; border-radius: 10px; font-size: 0.92rem; font-weight: 500; }
.alert-success { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
.alert-error { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
.alert-info { background: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
.alert-close { background: transparent; border: none; font-size: 1.2rem; cursor: pointer; color: inherit; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }
.stat-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.35rem; }
.stat-label { font-size: 0.85rem; color: #64748b; font-weight: 500; }
.stat-value { font-size: 1.75rem; }
.stat-value.accent { color: #2563eb; }
.stat-hint { font-size: 0.78rem; color: #94a3b8; }
.panels-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.25rem; }
.panel { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.5rem; }
.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.25rem; }
.panel-header h2 { margin: 0; font-size: 1.15rem; }
.fn-chip { font-family: ui-monospace, monospace; font-size: 0.78rem; background: #f1f5f9; padding: 0.2rem 0.55rem; border-radius: 6px; border: 1px solid #cbd5e1; }
.panel-desc { margin: 0 0 1.25rem; font-size: 0.88rem; color: #64748b; }
.form-stack { display: flex; flex-direction: column; gap: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.88rem; font-weight: 500; }
.field input { padding: 0.65rem 0.8rem; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 0.95rem; }
.summary-row { display: flex; align-items: center; justify-content: space-between; background: #f8fafc; padding: 0.75rem 0.9rem; border-radius: 10px; font-size: 0.9rem; }
.btn { border: none; border-radius: 10px; padding: 0.7rem 1.15rem; font-size: 0.95rem; font-weight: 600; cursor: pointer; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-secondary { background: #0f172a; color: #fff; }
.btn-full { width: 100%; }
```

---

## PHẦN 4: CHẠY ỨNG DỤNG & KIỂM THỬ NGHIỆP VỤ

### Bước 4.1: Chạy Frontend

Trong Terminal của VS Code (đang ở thư mục `frontend`), chạy:

```bash
npm run dev
```

Mở trình duyệt theo địa chỉ hiển thị (thường là `http://localhost:5173`).

### Bước 4.2: Kịch bản kiểm thử (Checklist nộp bài)

Chuẩn bị **2 tài khoản trên MetaMask** (Account 1 là **Điều hành** đã deploy contract, Account 2 là **Khách hàng**):

1. **Kết nối ví:** Nhấn **Kết nối MetaMask**, kiểm tra hiển thị đúng địa chỉ ví, số dư ETH và nhãn vai trò.
2. **Tạo tour (`createTour()`):**
   - Dùng ví **Điều hành**: nhập `25` chỗ, giá `0.08` ETH → nhấn **Tạo / Mở lại Tour** → xác nhận MetaMask → kiểm tra chỗ trống hiển thị `25 / 25`.
   - Thử đổi sang ví **Khách hàng** và bấm tạo tour → hệ thống phải báo lỗi không có quyền điều hành.
3. **Đặt chỗ hợp lệ (`bookSeats()`):**
   - Dùng ví **Khách hàng**: nhập `2` chỗ → hệ thống tính `0.16 ETH` → nhấn **Đặt chỗ ngay** → xác nhận MetaMask.
   - Kiểm tra `getAvailableSeats()` giảm còn `23 / 25` và `getMyBookings()` tăng lên `2 chỗ`.
4. **Kiểm tra ràng buộc lỗi:**
   - Nhập số chỗ `0` hoặc `-1` → phải bị chặn.
   - Nhập số chỗ lớn hơn `23` (vượt chỗ trống) → phải báo lỗi không đủ chỗ.
5. **Đổi ví khác để kiểm tra `getMyBookings()`:**
   - Chuyển sang ví thứ 3 chưa đặt vé → mục **Vé bạn đã đặt** phải hiển thị `0 chỗ` (chứng minh lưu đúng theo từng ví).
