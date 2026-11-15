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
            <p className="subtitle">Đặt vé du lịch minh bạch trên Web3 &amp; Solidity</p>
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
            <span className="stat-label">
              {isOperator ? "Số chỗ đã được đặt" : "Vé bạn đã đặt"}
            </span>
            <strong className="stat-value">
              {isOperator ? `${Math.max(totalSeats - availableSeats, 0)} chỗ` : `${myBookings} chỗ`}
            </strong>
            <span className="stat-hint">
              {isOperator ? "Tổng hợp toàn tour" : "Hàm: getMyBookings()"}
            </span>
          </div>
        </section>

        <section className="role-panel-wrap">
          {!account ? (
            <div className="panel panel-center">
              <h2>Chưa kết nối ví MetaMask</h2>
              <p className="panel-desc">
                Vui lòng kết nối ví MetaMask. Hệ thống sẽ tự động nhận diện bạn là{" "}
                <strong>Điều hành</strong> hay <strong>Khách hàng</strong> để hiển thị giao
                diện phù hợp.
              </p>
              <button className="btn btn-primary" onClick={handleConnectWallet} disabled={loading}>
                {loading ? "Đang kết nối..." : "Kết nối MetaMask ngay"}
              </button>
            </div>
          ) : isOperator ? (
            <div className="panel">
              <div className="panel-header">
                <h2>Giao diện Điều hành — Mở / Tạo Tour</h2>
                <span className="fn-chip">createTour()</span>
              </div>
              <p className="panel-desc">
                Bạn đang đăng nhập bằng ví Điều hành{" "}
                <code>{formatShortAddress(operatorAddress)}</code>.
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

                <button type="submit" className="btn btn-secondary btn-full" disabled={loading}>
                  {loading ? "Đang xử lý..." : "Tạo / Mở lại Tour"}
                </button>
              </form>
            </div>
          ) : (
            <div className="panel">
              <div className="panel-header">
                <h2>Giao diện Khách hàng — Đặt chỗ Tour</h2>
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
                  disabled={loading || availableSeats === 0}
                >
                  {availableSeats === 0
                    ? "Tour đã hết chỗ"
                    : loading
                    ? "Đang xử lý..."
                    : "Đặt chỗ ngay"}
                </button>
              </form>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;